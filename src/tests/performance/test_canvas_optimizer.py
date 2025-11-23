"""
Canvas性能优化器测试

测试Canvas性能优化器的功能和性能提升效果。

Author: Canvas Learning System Team
Version: 2.0
Created: 2025-01-22
"""

import pytest
import time
import json
import tempfile
import os
from typing import Dict, List

# Import the optimizer
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))
from canvas_performance_optimizer import (
    CanvasPerformanceOptimizer,
    read_canvas_optimized,
    write_canvas_optimized,
    batch_canvas_operations,
    get_canvas_optimizer,
    optimized_read_canvas,
    optimized_write_canvas
)


class TestCanvasPerformanceOptimizer:
    """Canvas性能优化器测试类"""

    @pytest.fixture
    def sample_canvas_data(self):
        """创建测试Canvas数据"""
        return {
            "nodes": [
                {
                    "id": "node-1",
                    "type": "text",
                    "text": "测试节点1",
                    "x": 100,
                    "y": 100,
                    "width": 300,
                    "height": 200,
                    "color": "1"
                },
                {
                    "id": "node-2",
                    "type": "text",
                    "text": "测试节点2",
                    "x": 500,
                    "y": 100,
                    "width": 300,
                    "height": 200,
                    "color": "2"
                }
            ],
            "edges": [
                {
                    "id": "edge-1",
                    "fromNode": "node-1",
                    "toNode": "node-2",
                    "fromSide": "right",
                    "toSide": "left"
                }
            ]
        }

    @pytest.fixture
    def large_canvas_data(self):
        """创建大规模Canvas数据"""
        canvas_data = {"nodes": [], "edges": []}

        # 创建100个节点
        for i in range(100):
            canvas_data["nodes"].append({
                "id": f"large-node-{i}",
                "type": "text",
                "text": f"大规模测试节点 {i}",
                "x": (i % 10) * 400,
                "y": (i // 10) * 300,
                "width": 350,
                "height": 250,
                "color": str((i % 5) + 1)
            })

        # 创建50条边
        for i in range(50):
            canvas_data["edges"].append({
                "id": f"large-edge-{i}",
                "fromNode": f"large-node-{i}",
                "toNode": f"large-node-{(i + 1) % 100}",
                "fromSide": "right",
                "toSide": "left"
            })

        return canvas_data

    def test_cache_functionality(self, sample_canvas_data):
        """测试缓存功能"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.canvas', delete=False) as f:
            json.dump(sample_canvas_data, f)
            temp_path = f.name

        try:
            optimizer = CanvasPerformanceOptimizer(cache_size=10)

            # 第一次读取（缓存未命中）
            start_time = time.time()
            data1 = optimizer.read_canvas_cached(temp_path)
            first_read_time = time.time() - start_time

            # 第二次读取（缓存命中）
            start_time = time.time()
            data2 = optimizer.read_canvas_cached(temp_path)
            second_read_time = time.time() - start_time

            # 验证缓存效果
            assert data1 == data2, "两次读取的数据应该相同"
            assert second_read_time < first_read_time, "缓存读取应该更快"

            # 验证统计信息
            stats = optimizer.get_performance_stats()
            assert stats["cache_hits"] == 1
            assert stats["cache_misses"] == 1
            assert stats["cache_hit_rate_percent"] == 50.0

        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_cache_eviction(self, sample_canvas_data):
        """测试缓存驱逐机制"""
        optimizer = CanvasPerformanceOptimizer(cache_size=2)

        # 创建多个临时文件
        temp_files = []
        for i in range(3):
            with tempfile.NamedTemporaryFile(mode='w', suffix='.canvas', delete=False) as f:
                modified_data = sample_canvas_data.copy()
                modified_data["nodes"][0]["id"] = f"node-{i}"
                json.dump(modified_data, f)
                temp_files.append(f.name)

        try:
            # 读取3个文件（超过缓存大小）
            for temp_path in temp_files:
                optimizer.read_canvas_cached(temp_path)

            stats = optimizer.get_performance_stats()
            assert stats["cache_size"] <= 2, "缓存大小应该被限制"

            # 验证最早的缓存被驱逐
            assert len(optimizer._file_cache) <= 2

        finally:
            for temp_path in temp_files:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)

    def test_atomic_write(self, sample_canvas_data):
        """测试原子写入功能"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.canvas', delete=False) as f:
            json.dump(sample_canvas_data, f)
            temp_path = f.name

        try:
            optimizer = CanvasPerformanceOptimizer()

            # 修改数据
            modified_data = sample_canvas_data.copy()
            modified_data["nodes"][0]["text"] = "修改后的文本"

            # 原子写入
            optimizer.write_canvas_optimized(temp_path, modified_data, atomic=True)

            # 验证写入结果
            with open(temp_path, 'r', encoding='utf-8') as f:
                saved_data = json.load(f)

            assert saved_data["nodes"][0]["text"] == "修改后的文本"

        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_batch_operations(self, sample_canvas_data):
        """测试批量操作"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.canvas', delete=False) as f:
            json.dump(sample_canvas_data, f)
            temp_path = f.name

        try:
            optimizer = CanvasPerformanceOptimizer()

            # 准备批量操作
            operations = [
                (temp_path, lambda data: data["nodes"].append({
                    "id": "batch-node-1",
                    "type": "text",
                    "text": "批量添加节点1",
                    "x": 200,
                    "y": 300,
                    "width": 300,
                    "height": 200,
                    "color": "1"
                })),
                (temp_path, lambda data: data["nodes"].append({
                    "id": "batch-node-2",
                    "type": "text",
                    "text": "批量添加节点2",
                    "x": 600,
                    "y": 300,
                    "width": 300,
                    "height": 200,
                    "color": "2"
                })),
                (temp_path, lambda data: data.update({"metadata": {"batch_processed": True}}))
            ]

            # 执行批量操作
            optimizer.batch_canvas_operations(operations)

            # 验证结果
            updated_data = optimizer.read_canvas_cached(temp_path)
            assert len(updated_data["nodes"]) == 4, "应该有4个节点"
            assert updated_data["metadata"]["batch_processed"] is True

            # 验证统计信息
            stats = optimizer.get_performance_stats()
            assert stats["batch_operations"] >= 1

        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_data_optimization(self, sample_canvas_data):
        """测试数据优化功能"""
        optimizer = CanvasPerformanceOptimizer()

        # 添加一些需要优化的数据
        unoptimized_data = sample_canvas_data.copy()
        unoptimized_data["nodes"][0]["empty_field"] = ""
        unoptimized_data["nodes"][0]["none_field"] = None
        unoptimized_data["nodes"][1]["extra_field"] = "额外数据"

        optimized_data = optimizer.optimize_canvas_data(unoptimized_data)

        # 验证优化效果
        assert "empty_field" not in optimized_data["nodes"][0], "空字段应该被移除"
        assert "none_field" not in optimized_data["nodes"][0], "None字段应该被移除"
        assert "extra_field" in optimized_data["nodes"][1], "非空字段应该被保留"

    def test_performance_improvement(self, large_canvas_data):
        """测试性能提升效果"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.canvas', delete=False) as f:
            json.dump(large_canvas_data, f)
            temp_path = f.name

        try:
            optimizer = CanvasPerformanceOptimizer()

            # 测试传统方式
            start_time = time.time()
            for _ in range(10):
                with open(temp_path, 'r', encoding='utf-8') as f:
                    json.load(f)
            traditional_time = time.time() - start_time

            # 测试优化方式
            start_time = time.time()
            for _ in range(10):
                optimizer.read_canvas_cached(temp_path)
            optimized_time = time.time() - start_time

            # 验证性能提升
            improvement_percentage = ((traditional_time - optimized_time) / traditional_time) * 100
            print(f"性能提升: {improvement_percentage:.1f}%")

            # 至少应该有一些性能提升（由于缓存）
            assert optimized_time <= traditional_time, "优化版本应该不会比传统版本慢"

        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_memory_usage(self, large_canvas_data):
        """测试内存使用情况"""
        import psutil

        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        optimizer = CanvasPerformanceOptimizer(cache_size=50)

        # 创建多个临时文件并加载到缓存
        temp_files = []
        for i in range(20):
            with tempfile.NamedTemporaryFile(mode='w', suffix='.canvas', delete=False) as f:
                modified_data = large_canvas_data.copy()
                modified_data["metadata"] = {"file_index": i}
                json.dump(modified_data, f)
                temp_files.append(f.name)

            # 加载到缓存
            optimizer.read_canvas_cached(f.name)

        try:
            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = final_memory - initial_memory

            # 验证内存使用合理
            assert memory_increase < 100, f"内存增长 {memory_increase:.1f}MB，超过100MB限制"

            # 验证缓存统计
            stats = optimizer.get_performance_stats()
            assert stats["cache_memory_usage_mb"] > 0, "应该有缓存内存使用"
            assert stats["cache_size"] > 0, "应该有缓存项目"

        finally:
            for temp_path in temp_files:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)

    def test_global_optimizer_functions(self, sample_canvas_data):
        """测试全局优化器函数"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.canvas', delete=False) as f:
            json.dump(sample_canvas_data, f)
            temp_path = f.name

        try:
            # 测试全局函数
            data1 = read_canvas_optimized(temp_path)
            write_canvas_optimized(temp_path, data1)
            data2 = read_canvas_optimized(temp_path)

            assert data1 == data2, "读写数据应该一致"

            # 测试单例模式
            optimizer1 = get_canvas_optimizer()
            optimizer2 = get_canvas_optimizer()
            assert optimizer1 is optimizer2, "应该返回同一个实例"

        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_monitoring_decorator(self, sample_canvas_data):
        """测试性能监控装饰器"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.canvas', delete=False) as f:
            json.dump(sample_canvas_data, f)
            temp_path = f.name

        try:
            # 使用装饰器函数
            data1 = optimized_read_canvas(temp_path)
            optimized_write_canvas(temp_path, data1)
            data2 = optimized_read_canvas(temp_path)

            assert data1 == data2, "读写数据应该一致"

            # 检查性能统计
            optimizer = get_canvas_optimizer()
            if hasattr(optimizer, '_operation_times'):
                assert 'canvas_read' in optimizer._operation_times
                assert 'canvas_write' in optimizer._operation_times

        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_cache_invalidation(self, sample_canvas_data):
        """测试缓存失效机制"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.canvas', delete=False) as f:
            json.dump(sample_canvas_data, f)
            temp_path = f.name

        try:
            optimizer = CanvasPerformanceOptimizer()

            # 第一次读取（加载到缓存）
            data1 = optimizer.read_canvas_cached(temp_path)

            # 修改文件
            time.sleep(0.1)  # 确保文件时间戳不同
            modified_data = sample_canvas_data.copy()
            modified_data["nodes"][0]["text"] = "文件已修改"
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(modified_data, f)

            # 再次读取（应该检测到文件变化，重新加载）
            data2 = optimizer.read_canvas_cached(temp_path)

            # 验证获取了最新数据
            assert data2["nodes"][0]["text"] == "文件已修改"
            assert data1["nodes"][0]["text"] != data2["nodes"][0]["text"]

        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])