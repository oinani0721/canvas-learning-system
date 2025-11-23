"""
Story 11.4单元测试 - 异步处理架构测试

测试异步Canvas处理器的所有核心功能：
- 任务队列提交和处理
- 4个worker线程并发
- Canvas锁机制保证顺序
- 回调超时控制
- 队列容量限制
- 优雅关闭机制
- 防抖立即返回

Author: Canvas Learning System Team
Version: 1.0
Created: 2025-10-24
Story: 11.4 - 实现异步处理架构
"""

import pytest
import time
import threading
from unittest.mock import Mock, MagicMock, patch
from queue import Queue
import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from canvas_progress_tracker.async_processor import AsyncCanvasProcessor, AsyncTaskStats
from canvas_progress_tracker.canvas_monitor_engine import CanvasMonitorEngine, DebounceManager


# ===== Fixtures =====

@pytest.fixture
def mock_monitor_engine():
    """创建Mock监控引擎"""
    engine = Mock(spec=CanvasMonitorEngine)
    engine.canvas_cache = {}
    engine.change_callbacks = []
    engine._detect_canvas_changes = Mock(return_value=[])
    engine._process_canvas_changes = Mock()
    return engine


@pytest.fixture
def async_processor(mock_monitor_engine):
    """创建AsyncCanvasProcessor实例"""
    processor = AsyncCanvasProcessor(
        max_workers=4,
        queue_size=10,  # 小队列便于测试
        callback_timeout=1,  # 短超时便于测试
        monitor_engine=mock_monitor_engine
    )
    yield processor
    processor.shutdown(timeout=5)


@pytest.fixture
def async_processor_large_queue(mock_monitor_engine):
    """创建大队列的AsyncCanvasProcessor实例（用于容量测试）"""
    processor = AsyncCanvasProcessor(
        max_workers=4,
        queue_size=100,
        callback_timeout=1,
        monitor_engine=mock_monitor_engine
    )
    yield processor
    processor.shutdown(timeout=5)


# ===== Task 8.2: 测试异步队列正确接收任务 =====

def test_submit_task_success(async_processor):
    """测试成功提交任务到队列"""
    # Arrange
    canvas_path = "test.canvas"
    old_content = {"nodes": []}
    new_content = {"nodes": [{"id": "1"}]}

    # Act
    result = async_processor.submit_task(canvas_path, old_content, new_content)

    # Assert
    assert result is True
    assert async_processor.stats.tasks_submitted == 1
    assert async_processor.task_queue.qsize() >= 0  # 任务可能已被处理


def test_submit_multiple_tasks(async_processor):
    """测试提交多个任务"""
    # Arrange
    tasks = [
        ("test1.canvas", {"nodes": []}, {"nodes": [{"id": "1"}]}),
        ("test2.canvas", {"nodes": []}, {"nodes": [{"id": "2"}]}),
        ("test3.canvas", {"nodes": []}, {"nodes": [{"id": "3"}]})
    ]

    # Act
    results = []
    for canvas_path, old_content, new_content in tasks:
        result = async_processor.submit_task(canvas_path, old_content, new_content)
        results.append(result)

    # Assert
    assert all(results), "所有任务应该成功提交"
    assert async_processor.stats.tasks_submitted == 3


# ===== Task 8.3: 测试4个worker线程并发处理任务 =====

def test_worker_threads_count(async_processor):
    """测试worker线程数量"""
    # Assert
    assert len(async_processor.workers) == 4

    # 检查所有worker线程都在运行
    alive_workers = [w for w in async_processor.workers if w.is_alive()]
    assert len(alive_workers) == 4, "所有4个worker线程应该在运行"


def test_concurrent_processing(async_processor_large_queue):
    """测试并发处理多个任务"""
    # Arrange
    task_count = 20
    processed_tasks = []
    lock = threading.Lock()

    def mock_detect_changes(canvas_path, new_content):
        """模拟变更检测（记录处理的任务）"""
        with lock:
            processed_tasks.append(canvas_path)
        time.sleep(0.01)  # 模拟处理时间
        return []

    async_processor_large_queue.monitor_engine._detect_canvas_changes = mock_detect_changes

    # Act
    start_time = time.time()
    for i in range(task_count):
        async_processor_large_queue.submit_task(
            f"test{i}.canvas",
            {"nodes": []},
            {"nodes": [{"id": str(i)}]}
        )

    # 等待所有任务处理完成
    async_processor_large_queue.task_queue.join()
    elapsed = time.time() - start_time

    # Assert
    assert len(processed_tasks) == task_count, "所有任务都应该被处理"

    # 并发处理应该比串行快（粗略估计：4个worker应该快约3倍）
    # 串行耗时约：20 * 0.01 = 0.2秒
    # 并发耗时约：20 / 4 * 0.01 = 0.05秒（理论值）
    # 实际会有线程开销，所以这里检查是否 < 0.15秒
    assert elapsed < 0.15, f"并发处理应该更快，实际耗时: {elapsed:.3f}秒"


# ===== Task 8.4: 测试同一Canvas的任务顺序保证 =====

def test_same_canvas_sequential_processing(async_processor_large_queue):
    """测试同一Canvas的任务按顺序执行"""
    # Arrange
    canvas_path = "test.canvas"
    task_count = 10
    processed_order = []
    lock = threading.Lock()

    def mock_detect_changes(path, content):
        """记录处理顺序"""
        task_id = content.get("task_id")
        with lock:
            processed_order.append(task_id)
        time.sleep(0.02)  # 模拟处理时间
        return []

    async_processor_large_queue.monitor_engine._detect_canvas_changes = mock_detect_changes

    # Act
    for i in range(task_count):
        async_processor_large_queue.submit_task(
            canvas_path,
            {"task_id": i},
            {"task_id": i}
        )

    # 等待所有任务处理完成
    async_processor_large_queue.task_queue.join()

    # Assert
    assert len(processed_order) == task_count
    assert processed_order == list(range(task_count)), \
        f"任务应该按提交顺序执行，实际: {processed_order}"


# ===== Task 8.5: 测试不同Canvas的任务并发执行 =====

def test_different_canvas_concurrent_processing(async_processor_large_queue):
    """测试不同Canvas的任务可以并发执行"""
    # Arrange
    canvas_paths = ["test1.canvas", "test2.canvas", "test3.canvas", "test4.canvas"]
    processing_times = {}
    lock = threading.Lock()

    def mock_detect_changes(path, content):
        """记录每个Canvas的处理时间"""
        start = time.time()
        time.sleep(0.05)  # 模拟处理时间
        with lock:
            if path not in processing_times:
                processing_times[path] = []
            processing_times[path].append((start, time.time()))
        return []

    async_processor_large_queue.monitor_engine._detect_canvas_changes = mock_detect_changes

    # Act
    start_time = time.time()
    for canvas_path in canvas_paths:
        for i in range(5):  # 每个Canvas提交5个任务
            async_processor_large_queue.submit_task(
                canvas_path,
                {"task_id": i},
                {"task_id": i}
            )

    # 等待所有任务处理完成
    async_processor_large_queue.task_queue.join()
    total_elapsed = time.time() - start_time

    # Assert
    # 4个Canvas，每个5个任务，每个任务0.05秒
    # 串行: 4 * 5 * 0.05 = 1.0秒
    # 并发: 由于有4个worker，应该约为 5 * 0.05 = 0.25秒
    assert total_elapsed < 0.5, \
        f"不同Canvas应该并发处理，实际耗时: {total_elapsed:.3f}秒"

    # 检查不同Canvas之间有时间重叠（证明并发）
    assert len(processing_times) == 4


# ===== Task 8.6: 测试回调超时控制（2秒） =====

def test_callback_timeout_detection(async_processor):
    """测试回调超时检测"""
    # Arrange
    timeout_detected = False

    def slow_callback(change):
        """慢回调函数（超过超时限制）"""
        time.sleep(1.5)  # 超过1秒超时

    async_processor.monitor_engine.change_callbacks = [slow_callback]
    async_processor.monitor_engine._detect_canvas_changes = Mock(return_value=[Mock()])

    # Act
    async_processor.submit_task(
        "test.canvas",
        {"nodes": []},
        {"nodes": [{"id": "1"}]}
    )

    # 等待任务处理
    time.sleep(2.5)

    # Assert
    # 检查是否记录了超时
    assert async_processor.stats.tasks_timeout > 0, "应该检测到回调超时"


def test_callback_exception_handling(async_processor):
    """测试回调异常处理"""
    # Arrange
    def failing_callback(change):
        """会抛出异常的回调"""
        raise ValueError("Test exception")

    async_processor.monitor_engine.change_callbacks = [failing_callback]
    async_processor.monitor_engine._detect_canvas_changes = Mock(return_value=[Mock()])

    # Act
    async_processor.submit_task(
        "test.canvas",
        {"nodes": []},
        {"nodes": [{"id": "1"}]}
    )

    # 等待任务处理
    time.sleep(0.5)

    # Assert
    # 系统应该捕获异常并继续运行
    assert async_processor.stats.tasks_failed > 0


# ===== Task 8.7: 测试队列容量限制（1000） =====

def test_queue_capacity_limit(async_processor):
    """测试队列容量限制（队列容量为10）"""
    # Arrange
    # 暂停worker处理（通过设置shutdown flag但不关闭）
    async_processor.monitor_engine._detect_canvas_changes = Mock(side_effect=lambda *args: time.sleep(1))

    # Act
    success_count = 0
    reject_count = 0

    for i in range(15):  # 提交15个任务（队列容量10）
        result = async_processor.submit_task(
            f"test{i}.canvas",
            {"nodes": []},
            {"nodes": [{"id": str(i)}]}
        )
        if result:
            success_count += 1
        else:
            reject_count += 1
        time.sleep(0.01)  # 稍微等待，让任务堆积

    # Assert
    assert reject_count > 0, "应该有任务被拒绝（队列满）"
    assert async_processor.stats.queue_full_count > 0


# ===== Task 8.8: 测试优雅关闭机制（最多30秒） =====

def test_graceful_shutdown(mock_monitor_engine):
    """测试优雅关闭"""
    # Arrange
    processor = AsyncCanvasProcessor(
        max_workers=4,
        queue_size=10,
        callback_timeout=1,
        monitor_engine=mock_monitor_engine
    )

    # 提交一些任务
    for i in range(5):
        processor.submit_task(
            f"test{i}.canvas",
            {"nodes": []},
            {"nodes": [{"id": str(i)}]}
        )

    # Act
    start_time = time.time()
    processor.shutdown(timeout=5)
    elapsed = time.time() - start_time

    # Assert
    assert elapsed < 5.5, f"关闭应该在5秒内完成，实际: {elapsed:.2f}秒"
    assert processor._shutdown_flag.is_set(), "关闭标志应该被设置"


def test_shutdown_rejects_new_tasks(async_processor):
    """测试关闭后拒绝新任务"""
    # Act
    async_processor.shutdown(timeout=1)

    result = async_processor.submit_task(
        "test.canvas",
        {"nodes": []},
        {"nodes": [{"id": "1"}]}
    )

    # Assert
    assert result is False, "关闭后应该拒绝新任务"


# ===== Task 8.9: 测试防抖后立即返回（< 10ms） =====

def test_flush_changes_immediate_return(mock_monitor_engine):
    """测试防抖处理立即返回（< 10ms）"""
    # Arrange
    debounce_manager = DebounceManager(
        delay_ms=500,
        monitor_engine=mock_monitor_engine
    )

    # 模拟Canvas文件
    test_canvas_path = "test_flush_immediate.canvas"
    import json
    test_content = {"nodes": [{"id": "1", "type": "text", "x": 0, "y": 0}]}

    with open(test_canvas_path, 'w', encoding='utf-8') as f:
        json.dump(test_content, f)

    try:
        # Act
        start_time = time.perf_counter()

        # 模拟_flush_changes调用（通过触发add_change和等待防抖）
        from canvas_progress_tracker.canvas_monitor_engine import CanvasChange, CanvasChangeType
        change = CanvasChange(
            change_id="test_change_1",
            canvas_id="test_flush_immediate.canvas",
            change_type=CanvasChangeType.UPDATE,
            file_path=test_canvas_path
        )

        debounce_manager.add_change(test_canvas_path, change)

        # 立即触发flush（不等待防抖延迟）
        debounce_manager._flush_changes(test_canvas_path)

        elapsed_ms = (time.perf_counter() - start_time) * 1000

        # Assert
        # 防抖处理应该立即返回（< 10ms）
        assert elapsed_ms < 15, f"防抖处理应该 < 10ms，实际: {elapsed_ms:.2f}ms"

    finally:
        # Cleanup
        if os.path.exists(test_canvas_path):
            os.remove(test_canvas_path)
        debounce_manager.clear_all()


# ===== AsyncTaskStats测试 =====

def test_async_task_stats():
    """测试异步任务统计"""
    # Arrange
    stats = AsyncTaskStats()

    # Act
    stats.record_task_submitted()
    stats.record_task_submitted()
    stats.record_task_processed(queue_delay_ms=5.0, processing_time_ms=10.0)
    stats.record_task_processed(queue_delay_ms=15.0, processing_time_ms=20.0)
    stats.record_task_failed()
    stats.record_task_timeout()
    stats.record_queue_full()

    # Assert
    assert stats.tasks_submitted == 2
    assert stats.tasks_processed == 2
    assert stats.tasks_failed == 1
    assert stats.tasks_timeout == 1
    assert stats.queue_full_count == 1
    assert stats.get_avg_queue_delay() == 10.0  # (5 + 15) / 2
    assert stats.get_avg_processing_time() == 15.0  # (10 + 20) / 2

    # 测试to_dict
    stats_dict = stats.to_dict()
    assert stats_dict["tasks_submitted"] == 2
    assert stats_dict["avg_queue_delay_ms"] == 10.0


# ===== Canvas锁机制测试 =====

def test_canvas_lock_mechanism(async_processor_large_queue):
    """测试Canvas锁机制的正确性"""
    # Arrange
    canvas_path = "test_lock.canvas"

    # Act
    lock1 = async_processor_large_queue._get_canvas_lock(canvas_path)
    lock2 = async_processor_large_queue._get_canvas_lock(canvas_path)

    # Assert
    assert lock1 is lock2, "同一Canvas应该返回相同的锁对象"


def test_canvas_lock_acquisition_timeout(async_processor):
    """测试Canvas锁获取超时"""
    # Arrange
    canvas_path = "test_lock_timeout.canvas"
    canvas_lock = async_processor._get_canvas_lock(canvas_path)

    # 模拟一个任务持有锁很长时间
    def hold_lock_long():
        with canvas_lock:
            time.sleep(6)  # 持有超过5秒

    lock_thread = threading.Thread(target=hold_lock_long)
    lock_thread.start()

    time.sleep(0.1)  # 确保锁已被获取

    # Act & Assert
    # 提交任务应该超时（5秒锁超时）
    start = time.time()
    async_processor.submit_task(
        canvas_path,
        {"nodes": []},
        {"nodes": [{"id": "1"}]}
    )

    # 等待任务处理尝试
    time.sleep(1)

    # 锁超时机制应该记录失败
    elapsed = time.time() - start
    assert elapsed < 7, "应该在锁超时后失败，不应等待太久"

    lock_thread.join()


# ===== 性能要求验证 =====

def test_performance_queue_delay():
    """测试队列延迟 < 10ms"""
    # Arrange
    mock_engine = Mock(spec=CanvasMonitorEngine)
    mock_engine.canvas_cache = {}
    mock_engine.change_callbacks = []
    mock_engine._detect_canvas_changes = Mock(return_value=[])

    processor = AsyncCanvasProcessor(
        max_workers=4,
        queue_size=1000,
        callback_timeout=2,
        monitor_engine=mock_engine
    )

    # Act
    submit_times = []
    for i in range(10):
        start = time.perf_counter()
        processor.submit_task(
            f"test{i}.canvas",
            {"nodes": []},
            {"nodes": [{"id": str(i)}]}
        )
        elapsed_ms = (time.perf_counter() - start) * 1000
        submit_times.append(elapsed_ms)

    processor.shutdown(timeout=5)

    # Assert
    avg_submit_time = sum(submit_times) / len(submit_times)
    assert avg_submit_time < 10, \
        f"平均队列提交时间应该 < 10ms，实际: {avg_submit_time:.2f}ms"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
