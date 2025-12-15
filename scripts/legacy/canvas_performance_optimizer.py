"""
Canvas性能优化模块

提供Canvas文件操作的性能优化功能，包括：
- 缓存机制
- 批量操作优化
- 异步I/O操作
- 内存优化

Author: Canvas Learning System Team
Version: 2.0
Created: 2025-01-22
"""

import json
import asyncio
import time
import threading
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import functools
import weakref


class CanvasPerformanceOptimizer:
    """Canvas性能优化器"""

    def __init__(self, cache_size: int = 100, enable_async: bool = True):
        self.cache_size = cache_size
        self.enable_async = enable_async

        # 文件内容缓存
        self._file_cache: Dict[str, Dict] = {}
        self._cache_timestamps: Dict[str, float] = {}
        self._cache_lock = threading.RLock()

        # 批量操作缓冲区
        self._batch_buffer: List[Tuple[str, callable]] = []
        self._batch_timer = None
        self._batch_timeout = 1.0  # 1秒批量提交

        # 性能统计
        self._performance_stats = {
            "cache_hits": 0,
            "cache_misses": 0,
            "batch_operations": 0,
            "total_operations": 0
        }

    def _should_cache_file(self, file_path: str) -> bool:
        """判断文件是否应该被缓存"""
        if not Path(file_path).exists():
            return False

        file_size = Path(file_path).stat().st_size
        # 只缓存小于1MB的文件
        return file_size < 1024 * 1024

    def _is_cache_valid(self, file_path: str, cache_time: float) -> bool:
        """检查缓存是否有效"""
        if not Path(file_path).exists():
            return False

        file_mtime = Path(file_path).stat().st_mtime
        return file_mtime <= cache_time

    def _evict_cache_if_needed(self):
        """在需要时驱逐缓存项"""
        if len(self._file_cache) >= self.cache_size:
            # 移除最旧的缓存项
            oldest_key = min(self._cache_timestamps.keys(),
                           key=lambda k: self._cache_timestamps[k])
            del self._file_cache[oldest_key]
            del self._cache_timestamps[oldest_key]

    def read_canvas_cached(self, canvas_path: str) -> Dict:
        """带缓存的Canvas文件读取"""
        self._performance_stats["total_operations"] += 1

        with self._cache_lock:
            # 检查缓存
            if (canvas_path in self._file_cache and
                canvas_path in self._cache_timestamps and
                self._is_cache_valid(canvas_path, self._cache_timestamps[canvas_path])):

                self._performance_stats["cache_hits"] += 1
                return self._file_cache[canvas_path].copy()

            # 缓存未命中，读取文件
            self._performance_stats["cache_misses"] += 1

            try:
                with open(canvas_path, 'r', encoding='utf-8') as f:
                    canvas_data = json.load(f)

                # 缓存文件内容
                if self._should_cache_file(canvas_path):
                    self._evict_cache_if_needed()
                    self._file_cache[canvas_path] = canvas_data.copy()
                    self._cache_timestamps[canvas_path] = time.time()

                return canvas_data

            except (FileNotFoundError, json.JSONDecodeError) as e:
                raise ValueError(f"无法读取Canvas文件 {canvas_path}: {e}")

    def write_canvas_optimized(self, canvas_path: str, canvas_data: Dict,
                             atomic: bool = True) -> None:
        """优化的Canvas文件写入"""
        self._performance_stats["total_operations"] += 1

        if atomic:
            # 原子写入：先写临时文件，再重命名
            temp_path = canvas_path + '.tmp'
            try:
                with open(temp_path, 'w', encoding='utf-8') as f:
                    json.dump(canvas_data, f, ensure_ascii=False, indent=2)

                # 原子重命名
                Path(temp_path).replace(canvas_path)

            except Exception as e:
                # 清理临时文件
                if Path(temp_path).exists():
                    Path(temp_path).unlink()
                raise e
        else:
            # 直接写入
            with open(canvas_path, 'w', encoding='utf-8') as f:
                json.dump(canvas_data, f, ensure_ascii=False, indent=2)

        # 更新缓存
        with self._cache_lock:
            if self._should_cache_file(canvas_path):
                self._evict_cache_if_needed()
                self._file_cache[canvas_path] = canvas_data.copy()
                self._cache_timestamps[canvas_path] = time.time()

    def batch_canvas_operations(self, operations: List[Tuple[str, callable]]) -> None:
        """批量Canvas操作"""
        self._performance_stats["batch_operations"] += 1

        # 按文件路径分组操作
        operations_by_file = {}
        for canvas_path, operation in operations:
            if canvas_path not in operations_by_file:
                operations_by_file[canvas_path] = []
            operations_by_file[canvas_path].append(operation)

        # 对每个文件执行批量操作
        for canvas_path, file_operations in operations_by_file.items():
            try:
                # 读取文件一次
                canvas_data = self.read_canvas_cached(canvas_path)

                # 执行所有操作
                for operation in file_operations:
                    operation(canvas_data)

                # 写入文件一次
                self.write_canvas_optimized(canvas_path, canvas_data)

            except Exception as e:
                print(f"批量操作失败 {canvas_path}: {e}")
                # 继续处理其他文件

    async def read_canvas_async(self, canvas_path: str) -> Dict:
        """异步读取Canvas文件"""
        if not self.enable_async:
            return self.read_canvas_cached(canvas_path)

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.read_canvas_cached, canvas_path)

    async def write_canvas_async(self, canvas_path: str, canvas_data: Dict) -> None:
        """异步写入Canvas文件"""
        if not self.enable_async:
            self.write_canvas_optimized(canvas_path, canvas_data)
            return

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self.write_canvas_optimized, canvas_path, canvas_data)

    def optimize_canvas_data(self, canvas_data: Dict) -> Dict:
        """优化Canvas数据结构"""
        optimized_data = canvas_data.copy()

        # 优化节点数据
        if "nodes" in optimized_data:
            optimized_nodes = []
            for node in optimized_data["nodes"]:
                # 移除空值和默认值
                optimized_node = {}
                for key, value in node.items():
                    if value is not None and value != "":
                        optimized_node[key] = value

                # 确保必需字段存在
                required_fields = ["id", "type", "x", "y", "width", "height"]
                for field in required_fields:
                    if field not in optimized_node:
                        if field in ["x", "y"]:
                            optimized_node[field] = 0
                        elif field in ["width", "height"]:
                            optimized_node[field] = 300
                        elif field == "type":
                            optimized_node[field] = "text"
                        elif field == "id":
                            optimized_node[field] = f"node-{int(time.time() * 1000)}"

                optimized_nodes.append(optimized_node)

            optimized_data["nodes"] = optimized_nodes

        # 优化边数据
        if "edges" in optimized_data:
            optimized_edges = []
            for edge in optimized_data["edges"]:
                # 移除空值
                optimized_edge = {k: v for k, v in edge.items() if v is not None and v != ""}

                # 确保必需字段存在
                required_fields = ["id", "fromNode", "toNode"]
                for field in required_fields:
                    if field not in optimized_edge:
                        if field == "id":
                            optimized_edge[field] = f"edge-{int(time.time() * 1000)}"
                        elif field in ["fromNode", "toNode"]:
                            # 如果缺少必需字段，跳过这条边
                            continue

                # 设置默认值
                if "fromSide" not in optimized_edge:
                    optimized_edge["fromSide"] = "right"
                if "toSide" not in optimized_edge:
                    optimized_edge["toSide"] = "left"

                optimized_edges.append(optimized_edge)

            optimized_data["edges"] = optimized_edges

        return optimized_data

    def clear_cache(self, file_path: Optional[str] = None) -> None:
        """清理缓存"""
        with self._cache_lock:
            if file_path:
                # 清理特定文件的缓存
                self._file_cache.pop(file_path, None)
                self._cache_timestamps.pop(file_path, None)
            else:
                # 清理所有缓存
                self._file_cache.clear()
                self._cache_timestamps.clear()

    def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计信息"""
        total_ops = self._performance_stats["total_operations"]
        cache_hit_rate = 0

        if total_ops > 0:
            cache_hit_rate = (self._performance_stats["cache_hits"] / total_ops) * 100

        return {
            **self._performance_stats,
            "cache_hit_rate_percent": round(cache_hit_rate, 2),
            "cache_size": len(self._file_cache),
            "cache_memory_usage_mb": round(self._estimate_cache_memory_usage(), 2)
        }

    def _estimate_cache_memory_usage(self) -> float:
        """估算缓存内存使用量（MB）"""
        import sys

        total_size = 0
        for canvas_data in self._file_cache.values():
            total_size += sys.getsizeof(canvas_data)

        return total_size / (1024 * 1024)  # 转换为MB

    def preload_cache(self, canvas_paths: List[str]) -> None:
        """预加载缓存"""
        for canvas_path in canvas_paths:
            try:
                self.read_canvas_cached(canvas_path)
            except Exception as e:
                print(f"预加载失败 {canvas_path}: {e}")


# 全局性能优化器实例
_global_optimizer: Optional[CanvasPerformanceOptimizer] = None


def get_canvas_optimizer() -> CanvasPerformanceOptimizer:
    """获取全局Canvas性能优化器实例"""
    global _global_optimizer
    if _global_optimizer is None:
        _global_optimizer = CanvasPerformanceOptimizer()
    return _global_optimizer


def read_canvas_optimized(canvas_path: str) -> Dict:
    """读取Canvas文件（优化版本）"""
    return get_canvas_optimizer().read_canvas_cached(canvas_path)


def write_canvas_optimized(canvas_path: str, canvas_data: Dict) -> None:
    """写入Canvas文件（优化版本）"""
    get_canvas_optimizer().write_canvas_optimized(canvas_path, canvas_data)


def batch_canvas_operations(operations: List[Tuple[str, callable]]) -> None:
    """批量Canvas操作（优化版本）"""
    get_canvas_optimizer().batch_canvas_operations(operations)


# 性能监控装饰器
def monitor_performance(operation_name: str):
    """性能监控装饰器"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time

                # 记录性能数据
                optimizer = get_canvas_optimizer()
                if not hasattr(optimizer, '_operation_times'):
                    optimizer._operation_times = {}

                if operation_name not in optimizer._operation_times:
                    optimizer._operation_times[operation_name] = []
                optimizer._operation_times[operation_name].append(execution_time)

                return result

            except Exception as e:
                execution_time = time.time() - start_time
                print(f"操作 {operation_name} 失败，耗时 {execution_time:.3f}s: {e}")
                raise

        return wrapper
    return decorator


@monitor_performance("canvas_read")
def optimized_read_canvas(canvas_path: str) -> Dict:
    """带性能监控的Canvas读取"""
    return read_canvas_optimized(canvas_path)


@monitor_performance("canvas_write")
def optimized_write_canvas(canvas_path: str, canvas_data: Dict) -> None:
    """带性能监控的Canvas写入"""
    return write_canvas_optimized(canvas_path, canvas_data)