"""
Canvas性能测试框架

该模块提供完整的Canvas布局系统性能测试和基准建立功能，
支持多种复杂度级别的Canvas文件测试和性能分析。

Author: Canvas Learning System Team
Version: 1.0
Created: 2025-10-22
"""

import gc
import json
import math
import os
import tempfile
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import psutil

try:
    import jinja2
    JINJA2_ENABLED = True
except ImportError:
    JINJA2_ENABLED = False
    print("警告: Jinja2未安装，报告生成功能受限")

# 导入现有的canvas系统
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from canvas_utils import CanvasJSONOperator, LayoutOptimizer


@dataclass
class PerformanceTestResult:
    """性能测试结果数据模型"""
    test_name: str
    node_count: int
    edge_count: int
    processing_time_ms: float
    memory_usage_mb: float
    memory_peak_mb: float
    layout_quality_score: float
    overlap_count: int
    optimizations_applied: int
    success: bool
    error_message: Optional[str] = None
    test_timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class StressTestResult:
    """压力测试结果数据模型"""
    test_session_id: str
    node_counts: List[int]
    results: List[PerformanceTestResult]
    summary_statistics: Dict[str, Any]
    test_timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class TestEnvironment:
    """测试环境信息"""
    python_version: str
    platform: str
    cpu_count: int
    memory_gb: float
    canvas_utils_version: str = "v2.0"
    test_machine_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])


class MemoryMonitor:
    """内存使用监控器"""

    def __init__(self):
        self.process = psutil.Process()
        self.start_memory = None
        self.peak_memory = None
        self.measurements = []

    def start_monitoring(self):
        """开始内存监控"""
        gc.collect()  # 强制垃圾回收
        self.start_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        self.peak_memory = self.start_memory
        self.measurements = [self.start_memory]

    def update_peak(self):
        """更新内存峰值"""
        current_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        self.peak_memory = max(self.peak_memory, current_memory)
        self.measurements.append(current_memory)
        return current_memory

    def get_memory_usage(self) -> Tuple[float, float, float]:
        """获取内存使用情况 (当前, 峰值, 增长) MB"""
        current = self.update_peak()
        peak = self.peak_memory
        growth = current - self.start_memory if self.start_memory else 0
        return current, peak, growth


class TestCanvasGenerator:
    """测试Canvas数据生成器"""

    def __init__(self):
        self.color_distribution = {
            "1": 0.15,  # 红色节点
            "2": 0.35,  # 绿色节点
            "3": 0.25,  # 紫色节点
            "5": 0.15,  # 蓝色节点
            "6": 0.10   # 黄色节点
        }

    def generate_test_canvas(self,
                           node_count: int,
                           complexity: str = "medium",
                           output_path: Optional[str] = None) -> str:
        """
        生成指定节点数和复杂度的测试Canvas文件

        Args:
            node_count: 节点数量
            complexity: 复杂度级别 (simple/medium/complex/chaotic)
            output_path: 输出文件路径，如果为None则使用临时文件

        Returns:
            str: 生成的Canvas文件路径
        """
        if output_path is None:
            temp_dir = tempfile.mkdtemp()
            output_path = os.path.join(temp_dir, f"test_canvas_{node_count}_{complexity}.canvas")

        # 创建基础Canvas结构
        canvas_data = {
            "nodes": [],
            "edges": []
        }

        # 根据复杂度选择生成策略
        if complexity == "simple":
            nodes, edges = self._generate_simple_layout(node_count)
        elif complexity == "medium":
            nodes, edges = self._generate_medium_layout(node_count)
        elif complexity == "complex":
            nodes, edges = self._generate_complex_layout(node_count)
        elif complexity == "chaotic":
            nodes, edges = self._generate_chaotic_layout(node_count)
        else:
            raise ValueError(f"不支持的复杂度级别: {complexity}")

        canvas_data["nodes"] = nodes
        canvas_data["edges"] = edges

        # 写入文件
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(canvas_data, f, ensure_ascii=False, indent=2)

        return output_path

    def _generate_simple_layout(self, node_count: int) -> Tuple[List[Dict], List[Dict]]:
        """生成简单布局（网格分布）"""
        nodes = []
        edges = []

        # 计算网格尺寸
        cols = int(math.sqrt(node_count * 1.2))
        rows = (node_count + cols - 1) // cols

        # 生成节点
        for i in range(node_count):
            x = (i % cols) * 200 + 100
            y = (i // cols) * 150 + 100
            color = self._get_node_color()

            node = {
                "id": str(uuid.uuid4()),
                "x": x,
                "y": y,
                "width": 180,
                "height": 100,
                "color": color,
                "text": f"测试节点 {i+1}"
            }
            nodes.append(node)

        # 生成简单的边连接
        for i in range(node_count - 1):
            edge = {
                "id": str(uuid.uuid4()),
                "from": nodes[i]["id"],
                "to": nodes[i+1]["id"],
                "color": "1"
            }
            edges.append(edge)

        return nodes, edges

    def _generate_medium_layout(self, node_count: int) -> Tuple[List[Dict], List[Dict]]:
        """生成中等复杂布局（聚类分布）"""
        nodes = []
        edges = []

        # 创建3-5个聚类
        cluster_count = min(5, max(3, node_count // 20))
        nodes_per_cluster = node_count // cluster_count

        for cluster_id in range(cluster_count):
            # 聚类中心点
            center_x = (cluster_id % 3) * 600 + 300
            center_y = (cluster_id // 3) * 400 + 200

            # 在聚类内生成节点
            start_idx = cluster_id * nodes_per_cluster
            end_idx = min(start_idx + nodes_per_cluster, node_count)

            cluster_nodes = []
            for i in range(start_idx, end_idx):
                # 在聚类中心附近随机分布
                x = center_x + (hash(i) % 200 - 100)
                y = center_y + (hash(i*2) % 150 - 75)
                color = self._get_node_color()

                node = {
                    "id": str(uuid.uuid4()),
                    "x": x,
                    "y": y,
                    "width": 180,
                    "height": 100,
                    "color": color,
                    "text": f"聚类{cluster_id+1}-节点{i-start_idx+1}"
                }
                nodes.append(node)
                cluster_nodes.append(node)

            # 在聚类内连接节点
            for i in range(len(cluster_nodes) - 1):
                edge = {
                    "id": str(uuid.uuid4()),
                    "from": cluster_nodes[i]["id"],
                    "to": cluster_nodes[i+1]["id"],
                    "color": "1"
                }
                edges.append(edge)

        return nodes, edges

    def _generate_complex_layout(self, node_count: int) -> Tuple[List[Dict], List[Dict]]:
        """生成复杂布局（多层级结构）"""
        # 简化实现，基于中等布局增加更多连接
        nodes, edges = self._generate_medium_layout(node_count)

        # 添加跨聚类的连接
        for i in range(min(10, len(edges) // 3)):
            from_idx = hash(i * 7) % len(nodes)
            to_idx = hash(i * 13) % len(nodes)
            if from_idx != to_idx:
                edge = {
                    "id": str(uuid.uuid4()),
                    "from": nodes[from_idx]["id"],
                    "to": nodes[to_idx]["id"],
                    "color": "2"
                }
                edges.append(edge)

        return nodes, edges

    def _generate_chaotic_layout(self, node_count: int) -> Tuple[List[Dict], List[Dict]]:
        """生成混乱布局（随机分布和大量重叠）"""
        nodes = []
        edges = []

        # 生成随机位置节点，故意造成重叠
        for i in range(node_count):
            x = hash(i) % 400 + 50  # 集中在小区域内
            y = hash(i * 3) % 300 + 50
            color = self._get_node_color()

            node = {
                "id": str(uuid.uuid4()),
                "x": x,
                "y": y,
                "width": 180,
                "height": 100,
                "color": color,
                "text": f"混乱节点 {i+1}"
            }
            nodes.append(node)

        # 生成大量随机连接
        edge_count = min(node_count * 3, 200)
        for i in range(edge_count):
            from_idx = hash(i * 11) % node_count
            to_idx = hash(i * 17) % node_count
            if from_idx != to_idx:
                edge = {
                    "id": str(uuid.uuid4()),
                    "from": nodes[from_idx]["id"],
                    "to": nodes[to_idx]["id"],
                    "color": "1"
                }
                edges.append(edge)

        return nodes, edges

    def _get_node_color(self) -> str:
        """根据分布概率获取节点颜色"""
        import random
        rand_val = random.random()
        cumulative = 0
        for color, prob in self.color_distribution.items():
            cumulative += prob
            if rand_val <= cumulative:
                return color
        return "1"  # 默认红色


class CanvasPerformanceTester:
    """Canvas性能测试框架核心类"""

    def __init__(self, test_config: Dict = None):
        """初始化性能测试框架"""
        self.test_config = test_config or {}
        self.test_environment = self._get_test_environment()
        self.canvas_generator = TestCanvasGenerator()
        self.layout_optimizer = LayoutOptimizer()

        # 创建输出目录
        self.output_dir = Path("src/tests/fixtures/performance")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 测试结果存储
        self.test_results = []
        self.current_session_id = str(uuid.uuid4())[:8]

    def _get_test_environment(self) -> TestEnvironment:
        """获取测试环境信息"""
        import platform
        import sys

        return TestEnvironment(
            python_version=sys.version,
            platform=platform.system(),
            cpu_count=psutil.cpu_count(),
            memory_gb=psutil.virtual_memory().total / 1024 / 1024 / 1024
        )

    def generate_test_canvas(self,
                           node_count: int,
                           complexity: str = "medium") -> str:
        """
        生成指定节点数和复杂度的测试Canvas文件

        Args:
            node_count: 节点数量
            complexity: 复杂度级别 (simple/medium/complex/chaotic)

        Returns:
            str: 生成的Canvas文件路径
        """
        output_path = self.output_dir / f"test_canvas_{node_count}_{complexity}_{self.current_session_id}.canvas"
        return self.canvas_generator.generate_test_canvas(
            node_count, complexity, str(output_path)
        )

    def run_performance_test(self,
                           canvas_path: str,
                           test_config: Dict = None) -> PerformanceTestResult:
        """
        运行性能测试

        Args:
            canvas_path: Canvas文件路径
            test_config: 测试配置

        Returns:
            PerformanceTestResult: 详细的性能测试结果
        """
        config = test_config or {}
        test_name = config.get('test_name', f"performance_test_{uuid.uuid4().hex[:8]}")

        # 读取Canvas文件
        canvas_op = CanvasJSONOperator(canvas_path)
        canvas_data = canvas_op.read_canvas()

        node_count = len(canvas_data.get('nodes', []))
        edge_count = len(canvas_data.get('edges', []))

        # 开始性能监控
        memory_monitor = MemoryMonitor()
        memory_monitor.start_monitoring()

        start_time = time.perf_counter()

        try:
            # 执行布局优化
            result = self.layout_optimizer.optimize_layout(canvas_path)

            end_time = time.perf_counter()
            processing_time_ms = (end_time - start_time) * 1000

            # 获取内存使用情况
            current_memory, peak_memory, memory_growth = memory_monitor.get_memory_usage()

            # 计算布局质量评分（简化实现）
            layout_quality_score = self._calculate_layout_quality(canvas_path)

            # 统计重叠数量
            overlap_count = self._count_overlaps(canvas_path)

            # 获取优化应用数量
            optimizations_applied = getattr(result, 'optimizations_applied', 0)

            test_result = PerformanceTestResult(
                test_name=test_name,
                node_count=node_count,
                edge_count=edge_count,
                processing_time_ms=processing_time_ms,
                memory_usage_mb=current_memory,
                memory_peak_mb=peak_memory,
                layout_quality_score=layout_quality_score,
                overlap_count=overlap_count,
                optimizations_applied=optimizations_applied,
                success=True
            )

        except Exception as e:
            end_time = time.perf_counter()
            processing_time_ms = (end_time - start_time) * 1000
            current_memory, peak_memory, _ = memory_monitor.get_memory_usage()

            test_result = PerformanceTestResult(
                test_name=test_name,
                node_count=node_count,
                edge_count=edge_count,
                processing_time_ms=processing_time_ms,
                memory_usage_mb=current_memory,
                memory_peak_mb=peak_memory,
                layout_quality_score=0.0,
                overlap_count=0,
                optimizations_applied=0,
                success=False,
                error_message=str(e)
            )

        self.test_results.append(test_result)
        return test_result

    def run_stress_test(self,
                       node_counts: List[int],
                       iterations: int = 3) -> StressTestResult:
        """
        运行压力测试

        Args:
            node_counts: 要测试的节点数量列表
            iterations: 每个规模的重复测试次数

        Returns:
            StressTestResult: 压力测试结果汇总
        """
        results = []
        test_session_id = str(uuid.uuid4())[:8]

        for node_count in node_counts:
            for iteration in range(iterations):
                # 生成测试Canvas
                complexity = self._get_complexity_for_node_count(node_count)
                canvas_path = self.generate_test_canvas(node_count, complexity)

                try:
                    # 运行性能测试
                    result = self.run_performance_test(
                        canvas_path,
                        {
                            'test_name': f'stress_test_{node_count}nodes_iter{iteration+1}',
                            'session_id': test_session_id
                        }
                    )
                    results.append(result)

                except Exception as e:
                    # 创建失败结果
                    failed_result = PerformanceTestResult(
                        test_name=f'stress_test_{node_count}nodes_iter{iteration+1}',
                        node_count=node_count,
                        edge_count=0,
                        processing_time_ms=0.0,
                        memory_usage_mb=0.0,
                        memory_peak_mb=0.0,
                        layout_quality_score=0.0,
                        overlap_count=0,
                        optimizations_applied=0,
                        success=False,
                        error_message=str(e)
                    )
                    results.append(failed_result)

                finally:
                    # 清理临时文件
                    try:
                        if os.path.exists(canvas_path):
                            os.remove(canvas_path)
                    except:
                        pass

        # 计算汇总统计
        summary_statistics = self._calculate_summary_statistics(results)

        return StressTestResult(
            test_session_id=test_session_id,
            node_counts=node_counts,
            results=results,
            summary_statistics=summary_statistics
        )

    def monitor_memory_usage(self, canvas_path: str) -> Dict:
        """
        监控内存使用情况

        Returns:
            Dict: 内存使用统计信息
        """
        memory_monitor = MemoryMonitor()
        memory_monitor.start_monitoring()

        try:
            # 执行Canvas操作
            canvas_op = CanvasJSONOperator(canvas_path)
            canvas_data = canvas_op.read_canvas()

            # 模拟一些处理
            result = self.layout_optimizer.optimize_layout(canvas_path)

            # 获取内存使用情况
            current_memory, peak_memory, growth = memory_monitor.get_memory_usage()

            return {
                "canvas_path": canvas_path,
                "node_count": len(canvas_data.get('nodes', [])),
                "memory_usage_mb": current_memory,
                "memory_peak_mb": peak_memory,
                "memory_growth_mb": growth,
                "memory_measurements": memory_monitor.measurements,
                "memory_leak_detected": growth > 100,  # 100MB增长阈值
                "monitoring_timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            current_memory, peak_memory, _ = memory_monitor.get_memory_usage()
            return {
                "canvas_path": canvas_path,
                "node_count": 0,
                "memory_usage_mb": current_memory,
                "memory_peak_mb": peak_memory,
                "memory_growth_mb": 0,
                "error": str(e),
                "monitoring_timestamp": datetime.now().isoformat()
            }

    def _calculate_layout_quality(self, canvas_path: str) -> float:
        """计算布局质量评分"""
        try:
            canvas_op = CanvasJSONOperator(canvas_path)
            canvas_data = canvas_op.read_canvas()
            nodes = canvas_data.get('nodes', [])

            if not nodes:
                return 0.0

            # 简化质量评分：基于重叠数量和节点分布
            overlap_count = self._count_overlaps(canvas_path)
            overlap_penalty = min(overlap_count * 0.5, 5.0)

            # 计算节点分布均匀性
            x_positions = [node.get('x', 0) for node in nodes]
            y_positions = [node.get('y', 0) for node in nodes]

            x_variance = max(x_positions) - min(x_positions) if len(set(x_positions)) > 1 else 1
            y_variance = max(y_positions) - min(y_positions) if len(set(y_positions)) > 1 else 1

            distribution_score = min((x_variance + y_variance) / 1000, 5.0)

            quality_score = max(10.0 - overlap_penalty + distribution_score, 0.0)
            return min(quality_score, 10.0)

        except Exception:
            return 5.0  # 默认中等评分

    def _count_overlaps(self, canvas_path: str) -> int:
        """统计节点重叠数量"""
        try:
            canvas_op = CanvasJSONOperator(canvas_path)
            canvas_data = canvas_op.read_canvas()
            nodes = canvas_data.get('nodes', [])

            overlap_count = 0
            for i, node1 in enumerate(nodes):
                for node2 in nodes[i+1:]:
                    if self._nodes_overlap(node1, node2):
                        overlap_count += 1

            return overlap_count

        except Exception:
            return 0

    def _nodes_overlap(self, node1: Dict, node2: Dict) -> bool:
        """检查两个节点是否重叠"""
        x1, y1 = node1.get('x', 0), node1.get('y', 0)
        w1, h1 = node1.get('width', 180), node1.get('height', 100)

        x2, y2 = node2.get('x', 0), node2.get('y', 0)
        w2, h2 = node2.get('width', 180), node2.get('height', 100)

        return not (x1 + w1 < x2 or x2 + w2 < x1 or y1 + h1 < y2 or y2 + h2 < y1)

    def _get_complexity_for_node_count(self, node_count: int) -> str:
        """根据节点数量确定复杂度级别"""
        if node_count <= 50:
            return "simple"
        elif node_count <= 200:
            return "medium"
        elif node_count <= 500:
            return "complex"
        else:
            return "chaotic"

    def _calculate_summary_statistics(self, results: List[PerformanceTestResult]) -> Dict[str, Any]:
        """计算汇总统计信息"""
        successful_results = [r for r in results if r.success]

        if not successful_results:
            return {
                "total_tests": len(results),
                "successful_tests": 0,
                "failed_tests": len(results),
                "success_rate": 0.0
            }

        processing_times = [r.processing_time_ms for r in successful_results]
        memory_usages = [r.memory_usage_mb for r in successful_results]

        return {
            "total_tests": len(results),
            "successful_tests": len(successful_results),
            "failed_tests": len(results) - len(successful_results),
            "success_rate": len(successful_results) / len(results) * 100,
            "processing_time_stats": {
                "min_ms": min(processing_times),
                "max_ms": max(processing_times),
                "avg_ms": sum(processing_times) / len(processing_times),
                "median_ms": sorted(processing_times)[len(processing_times) // 2]
            },
            "memory_usage_stats": {
                "min_mb": min(memory_usages),
                "max_mb": max(memory_usages),
                "avg_mb": sum(memory_usages) / len(memory_usages),
                "median_mb": sorted(memory_usages)[len(memory_usages) // 2]
            },
            "node_count_range": {
                "min": min(r.node_count for r in successful_results),
                "max": max(r.node_count for r in successful_results),
                "avg": sum(r.node_count for r in successful_results) / len(successful_results)
            }
        }


class PerformanceReportGenerator:
    """性能报告生成器"""

    def __init__(self, template_dir: str = "tests/templates"):
        """
        初始化报告生成器

        Args:
            template_dir: 模板文件目录
        """
        self.template_dir = Path(template_dir)
        self.template_dir.mkdir(parents=True, exist_ok=True)

        # 初始化Jinja2环境
        if JINJA2_ENABLED:
            template_loader = jinja2.FileSystemLoader(str(self.template_dir))
            self.jinja_env = jinja2.Environment(
                loader=template_loader,
                autoescape=jinja2.select_autoescape(['html', 'xml'])
            )
        else:
            self.jinja_env = None
            print("警告: Jinja2未安装，HTML报告生成功能受限")

    def generate_performance_report(self,
                                   test_results: List[PerformanceTestResult],
                                   test_environment: TestEnvironment,
                                   regression_result = None,
                                   output_path: Optional[str] = None) -> str:
        """
        生成性能报告

        Args:
            test_results: 性能测试结果列表
            test_environment: 测试环境信息
            regression_result: 回归测试结果（可选）
            output_path: 输出文件路径，如果为None则自动生成

        Returns:
            str: 生成的报告文件路径
        """
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"tests/reports/performance_report_{timestamp}.html"

        # 确保输出目录存在
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # 计算汇总统计
        summary = self._calculate_summary_statistics(test_results)

        # 准备模板数据
        template_data = {
            "report_timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "session_id": test_results[0].test_name.split('_')[-1] if test_results else "unknown",
            "test_results": test_results,
            "test_environment": test_environment,
            "summary": summary,
            "regression_result": regression_result
        }

        # 生成HTML报告
        if self.jinja_env:
            html_content = self._generate_html_report(template_data)
        else:
            html_content = self._generate_simple_html_report(template_data)

        # 写入文件
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)

        # 生成JSON报告
        json_output_path = output_file.with_suffix('.json')
        self._generate_json_report(template_data, str(json_output_path))

        print(f"性能报告已生成: {output_file}")
        return str(output_file)

    def _calculate_summary_statistics(self, results: List[PerformanceTestResult]) -> Dict[str, Any]:
        """计算汇总统计信息"""
        if not results:
            return {
                "total_tests": 0,
                "successful_tests": 0,
                "failed_tests": 0,
                "success_rate": 0.0,
                "processing_time_stats": {},
                "memory_usage_stats": {},
                "node_count_range": {}
            }

        successful_results = [r for r in results if r.success]
        failed_results = [r for r in results if not r.success]

        processing_times = [r.processing_time_ms for r in successful_results]
        memory_usages = [r.memory_usage_mb for r in successful_results]

        summary = {
            "total_tests": len(results),
            "successful_tests": len(successful_results),
            "failed_tests": len(failed_results),
            "success_rate": len(successful_results) / len(results) * 100 if results else 0,
            "processing_time_stats": {},
            "memory_usage_stats": {},
            "node_count_range": {}
        }

        if processing_times:
            summary["processing_time_stats"] = {
                "min_ms": min(processing_times),
                "max_ms": max(processing_times),
                "avg_ms": sum(processing_times) / len(processing_times),
                "median_ms": sorted(processing_times)[len(processing_times) // 2],
                "p95_ms": sorted(processing_times)[int(len(processing_times) * 0.95)] if len(processing_times) > 1 else processing_times[0]
            }

        if memory_usages:
            summary["memory_usage_stats"] = {
                "min_mb": min(memory_usages),
                "max_mb": max(memory_usages),
                "avg_mb": sum(memory_usages) / len(memory_usages),
                "median_mb": sorted(memory_usages)[len(memory_usages) // 2]
            }

        if successful_results:
            node_counts = [r.node_count for r in successful_results]
            summary["node_count_range"] = {
                "min": min(node_counts),
                "max": max(node_counts),
                "avg": sum(node_counts) / len(node_counts)
            }

        return summary

    def _generate_html_report(self, template_data: Dict[str, Any]) -> str:
        """使用Jinja2模板生成HTML报告"""
        try:
            template = self.jinja_env.get_template("performance_report.html")
            return template.render(**template_data)
        except Exception as e:
            print(f"警告: HTML模板渲染失败，使用简化版本 - {e}")
            return self._generate_simple_html_report(template_data)

    def _generate_simple_html_report(self, template_data: Dict[str, Any]) -> str:
        """生成简化的HTML报告（不依赖Jinja2）"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Canvas性能测试报告</title>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background: #667eea; color: white; padding: 20px; text-align: center; }}
                .summary {{ display: flex; gap: 20px; margin: 20px 0; }}
                .metric {{ background: #f8f9fa; padding: 15px; border-radius: 5px; text-align: center; }}
                table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background: #f8f9fa; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Canvas性能测试报告</h1>
                <p>生成时间: {template_data['report_timestamp']}</p>
            </div>

            <div class="summary">
                <div class="metric">
                    <h3>{template_data['summary']['total_tests']}</h3>
                    <p>总测试数</p>
                </div>
                <div class="metric">
                    <h3>{template_data['summary']['success_rate']:.1f}%</h3>
                    <p>成功率</p>
                </div>
                <div class="metric">
                    <h3>{template_data['summary']['processing_time_stats'].get('avg_ms', 0):.0f}ms</h3>
                    <p>平均处理时间</p>
                </div>
            </div>

            <h2>测试结果</h2>
            <table>
                <thead>
                    <tr>
                        <th>测试名称</th>
                        <th>节点数</th>
                        <th>处理时间(ms)</th>
                        <th>内存使用(MB)</th>
                        <th>状态</th>
                    </tr>
                </thead>
                <tbody>
        """

        for result in template_data['test_results']:
            status = "✅ 成功" if result.success else "❌ 失败"
            html += f"""
                    <tr>
                        <td>{result.test_name}</td>
                        <td>{result.node_count}</td>
                        <td>{result.processing_time_ms:.1f}</td>
                        <td>{result.memory_usage_mb:.1f}</td>
                        <td>{status}</td>
                    </tr>
            """

        html += """
                </tbody>
            </table>
        </body>
        </html>
        """

        return html

    def _generate_json_report(self, template_data: Dict[str, Any], output_path: str) -> None:
        """生成JSON格式的详细报告"""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(template_data, f, ensure_ascii=False, indent=2, default=str)
        except Exception as e:
            print(f"警告: JSON报告生成失败 - {e}")


# 导出主要类
__all__ = [
    'CanvasPerformanceTester',
    'TestCanvasGenerator',
    'PerformanceTestResult',
    'StressTestResult',
    'MemoryMonitor',
    'PerformanceReportGenerator'
]
