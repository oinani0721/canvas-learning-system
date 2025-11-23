"""
简化的性能测试套件

测试基本的系统性能，不依赖复杂的canvas_utils模块。
用于验证性能测试框架是否正常工作。

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


class TestSimplePerformance:
    """简化性能测试类"""

    @pytest.fixture
    def sample_data(self):
        """创建测试数据"""
        return {
            "nodes": [{"id": f"node-{i}", "text": f"节点 {i}"} for i in range(100)],
            "metadata": {"created_at": "2025-01-22T10:00:00Z"}
        }

    def test_json_read_performance(self, sample_data):
        """测试JSON读取性能"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(sample_data, f)
            temp_path = f.name

        try:
            start_time = time.time()
            with open(temp_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            end_time = time.time()

            execution_time = end_time - start_time

            # 性能断言: JSON读取应该在100ms内完成
            assert execution_time < 0.1, f"JSON读取耗时 {execution_time*1000:.1f}ms，超过100ms限制"
            assert len(data["nodes"]) == 100

        finally:
            os.unlink(temp_path)

    def test_json_write_performance(self, sample_data):
        """测试JSON写入性能"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name

        try:
            start_time = time.time()
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(sample_data, f, ensure_ascii=False, indent=2)
            end_time = time.time()

            execution_time = end_time - start_time

            # 性能断言: JSON写入应该在100ms内完成
            assert execution_time < 0.1, f"JSON写入耗时 {execution_time*1000:.1f}ms，超过100ms限制"

            # 验证文件大小
            file_size = os.path.getsize(temp_path)
            assert file_size > 1000  # 文件应该有实际内容

        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_data_processing_performance(self, sample_data):
        """测试数据处理性能"""
        start_time = time.time()

        # 模拟数据处理操作
        processed_data = []
        for node in sample_data["nodes"]:
            processed_node = {
                "id": node["id"],
                "text": node["text"].upper(),  # 转换为大写
                "length": len(node["text"]),
                "processed": True
            }
            processed_data.append(processed_node)

        # 排序操作
        processed_data.sort(key=lambda x: x["length"], reverse=True)

        end_time = time.time()

        execution_time = end_time - start_time

        # 性能断言: 100个节点的数据处理应该在50ms内完成
        assert execution_time < 0.05, f"数据处理耗时 {execution_time*1000:.1f}ms，超过50ms限制"
        assert len(processed_data) == 100
        assert processed_data[0]["length"] >= processed_data[-1]["length"]  # 验证排序

    def test_string_operations_performance(self):
        """测试字符串操作性能"""
        # 创建大文本内容
        large_text = "这是一个性能测试文本。" * 1000

        start_time = time.time()

        # 执行各种字符串操作
        operations = [
            len(large_text),
            large_text.upper(),
            large_text.lower(),
            large_text.replace("性能", "performance"),
            large_text.split("。"),
            "。".join(large_text.split("。")[:10])
        ]

        end_time = time.time()

        execution_time = end_time - start_time

        # 性能断言: 字符串操作应该在10ms内完成
        assert execution_time < 0.01, f"字符串操作耗时 {execution_time*1000:.1f}ms，超过10ms限制"
        assert len(operations) == 6

    def test_memory_allocation_performance(self):
        """测试内存分配性能"""
        import psutil
        import gc

        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        start_time = time.time()

        # 创建大量对象
        large_list = []
        for i in range(10000):
            large_list.append({
                "id": i,
                "data": f"数据 {i}" * 10,
                "timestamp": time.time(),
                "nested": {
                    "level1": {"level2": {"level3": f"深度数据 {i}"}}
                }
            })

        # 执行一些操作
        processed_count = 0
        for item in large_list:
            if item["id"] % 100 == 0:
                processed_count += 1

        del large_list  # 释放内存
        gc.collect()  # 强制垃圾回收

        end_time = time.time()

        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory

        execution_time = end_time - start_time

        # 性能断言
        assert execution_time < 1.0, f"内存分配测试耗时 {execution_time:.3f}s，超过1秒限制"
        assert memory_increase < 50, f"内存增长 {memory_increase:.1f}MB，超过50MB限制"
        assert processed_count == 100  # 验证操作正确性

    def test_concurrent_operations_performance(self):
        """测试并发操作性能"""
        import threading
        import queue

        results_queue = queue.Queue()

        def worker_task(worker_id):
            """工作线程任务"""
            start_time = time.time()

            # 执行一些计算任务
            result = 0
            for i in range(100000):
                result += i * worker_id

            end_time = time.time()
            execution_time = end_time - start_time

            results_queue.put({
                "worker_id": worker_id,
                "result": result,
                "execution_time": execution_time
            })

        start_time = time.time()

        # 创建并启动多个线程
        threads = []
        for i in range(5):
            thread = threading.Thread(target=worker_task, args=(i + 1,))
            threads.append(thread)
            thread.start()

        # 等待所有线程完成
        for thread in threads:
            thread.join()

        end_time = time.time()
        total_time = end_time - start_time

        # 收集结果
        results = []
        while not results_queue.empty():
            results.append(results_queue.get())

        # 性能断言
        assert total_time < 5.0, f"并发操作耗时 {total_time:.3f}s，超过5秒限制"
        assert len(results) == 5, "应该有5个工作线程的结果"

        # 验证每个工作线程都正确执行
        for result in results:
            assert result["result"] > 0, "每个工作线程应该产生正数结果"
            assert result["execution_time"] < 1.0, "每个工作线程应该在1秒内完成"

    def test_file_io_performance(self):
        """测试文件I/O性能"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # 创建测试文件路径
            test_files = []
            for i in range(10):
                file_path = os.path.join(temp_dir, f"test_file_{i}.txt")
                test_files.append(file_path)

            start_time = time.time()

            # 写入操作
            for i, file_path in enumerate(test_files):
                content = f"这是测试文件 {i}\n" + "测试内容行\n" * 1000
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)

            # 读取操作
            total_lines = 0
            for file_path in test_files:
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    total_lines += len(lines)

            end_time = time.time()

            execution_time = end_time - start_time

            # 性能断言
            assert execution_time < 1.0, f"文件I/O操作耗时 {execution_time:.3f}s，超过1秒限制"
            assert total_lines == 10 * 1001, "应该读取到正确的行数"

    def test_performance_regression_simulation(self, sample_data):
        """模拟性能回归测试"""
        # 模拟基准性能
        baseline_time = 0.01  # 假设基准时间是10ms

        start_time = time.time()

        # 执行测试操作
        processed_items = []
        for node in sample_data["nodes"]:
            processed_item = {
                "original": node,
                "processed": f"已处理: {node['text']}",
                "timestamp": time.time()
            }
            processed_items.append(processed_item)

        end_time = time.time()
        current_time = end_time - start_time

        # 计算性能回归百分比
        regression_percentage = ((current_time - baseline_time) / baseline_time) * 100

        # 性能断言
        assert current_time < 0.05, f"当前性能 {current_time*1000:.1f}ms，超过50ms限制"
        assert regression_percentage < 100, f"性能回归 {regression_percentage:.1f}%，超过100%限制"
        assert len(processed_items) == 100, "应该处理所有项目"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])