"""
Canvas操作性能测试套件

测试Canvas文件读写、布局算法等核心操作的性能指标，
确保响应时间满足PRD要求（基础操作<3秒，复杂操作<10秒）。

Author: Canvas Learning System Team
Version: 2.0
Created: 2025-01-22
"""

import json
import os

# Import the canvas utils modules
import sys
import tempfile
import time
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).parent.parent.parent))
from canvas_utils import CanvasBusinessLogic, CanvasJSONOperator


class TestCanvasPerformance:
    """Canvas操作性能测试类"""

    @pytest.fixture
    def sample_canvas_data(self):
        """创建测试用的Canvas数据"""
        return {
            "nodes": [],
            "edges": []
        }

    @pytest.fixture
    def large_canvas_data(self):
        """创建大规模Canvas测试数据"""
        canvas_data = {"nodes": [], "edges": []}

        # 创建100个节点
        for i in range(100):
            canvas_data["nodes"].append({
                "id": f"test-node-{i}",
                "type": "text",
                "text": f"测试节点 {i} 的内容",
                "x": (i % 10) * 500,
                "y": (i // 10) * 400,
                "width": 400,
                "height": 300,
                "color": "1" if i % 3 == 0 else "2"
            })

        # 创建一些边连接
        for i in range(0, 90, 10):
            canvas_data["edges"].append({
                "id": f"edge-{i}",
                "fromNode": f"test-node-{i}",
                "toNode": f"test-node-{i+1}",
                "fromSide": "right",
                "toSide": "left"
            })

        return canvas_data

    def test_read_canvas_performance_small(self, sample_canvas_data):
        """测试读取小规模Canvas文件的性能 (< 1秒)"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.canvas', delete=False) as f:
            json.dump(sample_canvas_data, f)
            temp_path = f.name

        try:
            start_time = time.time()
            result = CanvasJSONOperator.read_canvas(temp_path)
            end_time = time.time()

            execution_time = end_time - start_time

            # 性能断言: 读取小文件应该在1秒内完成
            assert execution_time < 1.0, f"读取小Canvas文件耗时 {execution_time:.3f}s，超过1秒限制"
            assert "nodes" in result
            assert "edges" in result

        finally:
            os.unlink(temp_path)

    def test_read_canvas_performance_large(self, large_canvas_data):
        """测试读取大规模Canvas文件的性能 (< 2秒)"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.canvas', delete=False) as f:
            json.dump(large_canvas_data, f)
            temp_path = f.name

        try:
            start_time = time.time()
            result = CanvasJSONOperator.read_canvas(temp_path)
            end_time = time.time()

            execution_time = end_time - start_time

            # 性能断言: 读取大文件应该在2秒内完成
            assert execution_time < 2.0, f"读取大Canvas文件耗时 {execution_time:.3f}s，超过2秒限制"
            assert len(result["nodes"]) == 100
            assert len(result["edges"]) == 9

        finally:
            os.unlink(temp_path)

    def test_write_canvas_performance_small(self, sample_canvas_data):
        """测试写入小规模Canvas文件的性能 (< 1秒)"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.canvas', delete=False) as f:
            temp_path = f.name

        try:
            start_time = time.time()
            CanvasJSONOperator.write_canvas(temp_path, sample_canvas_data)
            end_time = time.time()

            execution_time = end_time - start_time

            # 性能断言: 写入小文件应该在1秒内完成
            assert execution_time < 1.0, f"写入小Canvas文件耗时 {execution_time:.3f}s，超过1秒限制"

            # 验证文件写入正确
            with open(temp_path, 'r', encoding='utf-8') as f:
                saved_data = json.load(f)
            assert saved_data == sample_canvas_data

        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_write_canvas_performance_large(self, large_canvas_data):
        """测试写入大规模Canvas文件的性能 (< 2秒)"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.canvas', delete=False) as f:
            temp_path = f.name

        try:
            start_time = time.time()
            CanvasJSONOperator.write_canvas(temp_path, large_canvas_data)
            end_time = time.time()

            execution_time = end_time - start_time

            # 性能断言: 写入大文件应该在2秒内完成
            assert execution_time < 2.0, f"写入大Canvas文件耗时 {execution_time:.3f}s，超过2秒限制"

        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_layout_algorithm_performance_50_nodes(self):
        """测试50个节点的布局算法性能 (< 1秒)"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.canvas', delete=False) as f:
            canvas_data = {"nodes": [], "edges": []}

            # 创建50个测试节点
            for i in range(50):
                canvas_data["nodes"].append({
                    "id": f"layout-test-{i}",
                    "type": "text",
                    "text": f"布局测试节点 {i}",
                    "x": 0,
                    "y": 0,
                    "width": 400,
                    "height": 300,
                    "color": "1"
                })

            json.dump(canvas_data, f)
            temp_path = f.name

        try:
            business_logic = CanvasBusinessLogic(temp_path)

            start_time = time.time()

            # 对第一个节点添加问题和黄色理解节点，触发布局算法
            question_id, yellow_id = business_logic.add_sub_question_with_yellow_node(
                "layout-test-0",
                "这是一个布局性能测试问题",
                "💡 提示：测试布局算法性能"
            )

            end_time = time.time()

            execution_time = end_time - start_time

            # 性能断言: 50节点布局应该在1秒内完成
            assert execution_time < 1.0, f"50节点布局算法耗时 {execution_time:.3f}s，超过1秒限制"
            assert question_id is not None
            assert yellow_id is not None

        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_layout_algorithm_performance_200_nodes(self):
        """测试200个节点的布局算法性能 (< 3秒)"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.canvas', delete=False) as f:
            canvas_data = {"nodes": [], "edges": []}

            # 创建200个测试节点
            for i in range(200):
                canvas_data["nodes"].append({
                    "id": f"layout-test-{i}",
                    "type": "text",
                    "text": f"布局测试节点 {i}",
                    "x": 0,
                    "y": 0,
                    "width": 400,
                    "height": 300,
                    "color": "1"
                })

            json.dump(canvas_data, f)
            temp_path = f.name

        try:
            business_logic = CanvasBusinessLogic(temp_path)

            start_time = time.time()

            # 对第一个节点添加问题和黄色理解节点，触发布局算法
            question_id, yellow_id = business_logic.add_sub_question_with_yellow_node(
                "layout-test-0",
                "这是一个大规模布局性能测试问题",
                "💡 提示：测试大规模布局算法性能"
            )

            end_time = time.time()

            execution_time = end_time - start_time

            # 性能断言: 200节点布局应该在3秒内完成
            assert execution_time < 3.0, f"200节点布局算法耗时 {execution_time:.3f}s，超过3秒限制"
            assert question_id is not None
            assert yellow_id is not None

        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_batch_node_operations_performance(self):
        """测试批量节点操作性能"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.canvas', delete=False) as f:
            json.dump({"nodes": [], "edges": []}, f)
            temp_path = f.name

        try:
            canvas_data = CanvasJSONOperator.read_canvas(temp_path)

            start_time = time.time()

            # 批量创建50个节点
            node_ids = []
            for i in range(50):
                node_id = CanvasJSONOperator.create_node(
                    canvas_data,
                    node_type="text",
                    x=(i % 10) * 500,
                    y=(i // 10) * 400,
                    text=f"批量创建节点 {i}"
                )
                node_ids.append(node_id)

            # 一次性写入所有节点
            CanvasJSONOperator.write_canvas(temp_path, canvas_data)

            end_time = time.time()

            execution_time = end_time - start_time

            # 性能断言: 批量操作50个节点应该在2秒内完成
            assert execution_time < 2.0, f"批量创建50个节点耗时 {execution_time:.3f}s，超过2秒限制"
            assert len(node_ids) == 50
            assert len(canvas_data["nodes"]) == 50

        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_memory_usage_canvas_operations(self, large_canvas_data):
        """测试Canvas操作的内存使用情况"""
        import gc

        import psutil

        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        with tempfile.NamedTemporaryFile(mode='w', suffix='.canvas', delete=False) as f:
            json.dump(large_canvas_data, f)
            temp_path = f.name

        try:
            # 执行多次读写操作
            for _ in range(10):
                canvas_data = CanvasJSONOperator.read_canvas(temp_path)

                # 模拟一些处理操作
                for node in canvas_data["nodes"]:
                    node["text"] += " (processed)"

                CanvasJSONOperator.write_canvas(temp_path, canvas_data)

            gc.collect()  # 强制垃圾回收

            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = final_memory - initial_memory

            # 内存增长应该在合理范围内（< 100MB）
            assert memory_increase < 100, f"内存使用增长 {memory_increase:.1f}MB，超过100MB限制"

        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
