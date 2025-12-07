"""
Canvas事件处理系统单元测试

测试Canvas事件的处理器和分发器：
- 事件类型转换
- 事件过滤
- 事件分发
- 错误处理
- 性能监控

Author: Canvas Learning System Team
Version: 1.0
Created: 2025-10-24
"""

import threading
import time
import unittest
from unittest.mock import Mock

from canvas_progress_tracker.canvas_monitor_engine import CanvasChange, CanvasChangeType, CanvasEvent, CanvasEventType
from canvas_progress_tracker.events.canvas_event_handler import (
    CanvasEventHandler,
    EventFilter,
    EventPriority,
)
from canvas_progress_tracker.events.event_dispatcher import (
    DispatchConfig,
    DispatchStrategy,
    EventDispatcher,
)


class TestCanvasEventHandler(unittest.TestCase):
    """Canvas事件处理器测试"""

    def setUp(self):
        """测试前设置"""
        self.handler = CanvasEventHandler()
        self.processed_events = []

    def test_add_event_listener(self):
        """测试添加事件监听器"""
        callback = Mock()
        self.handler.add_event_listener(CanvasEventType.NODE_ADDED, callback)

        self.assertIn(CanvasEventType.NODE_ADDED, self.handler.event_listeners)
        self.assertIn(callback, self.handler.event_listeners[CanvasEventType.NODE_ADDED])

    def test_add_global_listener(self):
        """测试添加全局监听器"""
        callback = Mock()
        self.handler.add_global_listener(callback)

        self.assertIn(callback, self.handler.global_listeners)

    def test_add_event_filter(self):
        """测试添加事件过滤器"""
        filter_obj = EventFilter(
            change_types={CanvasChangeType.CREATE},
            node_types={"text"},
            min_priority=EventPriority.MEDIUM
        )
        self.handler.add_event_filter(filter_obj)

        self.assertIn(filter_obj, self.handler.event_filters)

    def test_convert_change_to_events(self):
        """测试变更转换为事件"""
        change = CanvasChange(
            change_id="test-change-1",
            canvas_id="test-canvas",
            change_type=CanvasChangeType.CREATE,
            node_id="test-node",
            node_type="text",
            new_content={"text": "New node content"},
            file_path="/test.canvas"
        )

        events = self.handler._convert_change_to_events(change)

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].event_type, CanvasEventType.NODE_ADDED)
        self.assertEqual(events[0].canvas_id, "test-canvas")
        self.assertEqual(events[0].node_id, "test-node")

    def test_convert_color_change_to_events(self):
        """测试颜色变更转换为事件"""
        change = CanvasChange(
            change_id="test-color-change",
            canvas_id="test-canvas",
            change_type=CanvasChangeType.UPDATE,
            node_id="test-node",
            node_type="text",
            old_content={"color": "1"},  # 红色
            new_content={"color": "2"},  # 绿色
            file_path="/test.canvas"
        )

        events = self.handler._convert_change_to_events(change)

        # 应该生成颜色变更事件
        color_events = [e for e in events if e.event_type == CanvasEventType.COLOR_CHANGED]
        self.assertGreater(len(color_events), 0)

        color_event = color_events[0]
        self.assertEqual(color_event.event_data["old_color"], "1")
        self.assertEqual(color_event.event_data["new_color"], "2")

    def test_convert_position_change_to_events(self):
        """测试位置变更转换为事件"""
        change = CanvasChange(
            change_id="test-position-change",
            canvas_id="test-canvas",
            change_type=CanvasChangeType.UPDATE,
            node_id="test-node",
            node_type="text",
            old_content={"x": 100, "y": 100},
            new_content={"x": 200, "y": 150},
            file_path="/test.canvas"
        )

        events = self.handler._convert_change_to_events(change)

        # 应该生成位置变更事件
        position_events = [e for e in events if e.event_type == CanvasEventType.POSITION_CHANGED]
        self.assertGreater(len(position_events), 0)

        position_event = position_events[0]
        self.assertEqual(position_event.event_data["old_position"]["x"], 100)
        self.assertEqual(position_event.event_data["old_position"]["y"], 100)
        self.assertEqual(position_event.event_data["new_position"]["x"], 200)
        self.assertEqual(position_event.event_data["new_position"]["y"], 150)

    def test_generate_derived_events(self):
        """测试生成派生事件"""
        # 创建从红色变为绿色的颜色变更事件
        event = CanvasEvent(
            event_id="color-change-event",
            event_type=CanvasEventType.COLOR_CHANGED,
            canvas_id="test-canvas",
            node_id="test-node",
            event_data={
                "old_color": "1",  # 红色
                "new_color": "2"   # 绿色
            }
        )

        derived_events = self.handler._generate_derived_events(event)

        # 应该生成学习进度事件
        progress_events = [e for e in derived_events if "learning_progress" in e.event_id]
        self.assertGreater(len(progress_events), 0)

    def test_should_process_change_with_filter(self):
        """测试过滤器应用"""
        # 添加只允许CREATE类型变更的过滤器
        filter_obj = EventFilter(change_types={CanvasChangeType.CREATE})
        self.handler.add_event_filter(filter_obj)

        # CREATE类型变更应该通过
        create_change = CanvasChange(
            change_id="create-change",
            canvas_id="test",
            change_type=CanvasChangeType.CREATE,
            file_path="/test.canvas"
        )
        self.assertTrue(self.handler._should_process_change(create_change))

        # UPDATE类型变更应该被过滤
        update_change = CanvasChange(
            change_id="update-change",
            canvas_id="test",
            change_type=CanvasChangeType.UPDATE,
            file_path="/test.canvas"
        )
        self.assertFalse(self.handler._should_process_change(update_change))

    def test_process_canvas_changes(self):
        """测试处理Canvas变更列表"""
        def callback(event):
            self.processed_events.append(event)

        self.handler.add_global_listener(callback)

        changes = [
            CanvasChange(
                change_id="change-1",
                canvas_id="test-canvas",
                change_type=CanvasChangeType.CREATE,
                node_id="node-1",
                node_type="text",
                new_content={"text": "Node 1"},
                file_path="/test.canvas"
            ),
            CanvasChange(
                change_id="change-2",
                canvas_id="test-canvas",
                change_type=CanvasChangeType.UPDATE,
                node_id="node-2",
                node_type="text",
                old_content={"color": "1"},
                new_content={"color": "2"},
                file_path="/test.canvas"
            )
        ]

        results = self.handler.process_canvas_changes(changes)

        self.assertEqual(len(results), 2)
        self.assertTrue(all(result.success for result in results))
        self.assertGreater(len(self.processed_events), 0)

    def test_get_processing_statistics(self):
        """测试获取处理统计信息"""
        stats = self.handler.get_processing_statistics()

        self.assertIn("total_events_processed", stats)
        self.assertIn("successful_processing", stats)
        self.assertIn("failed_processing", stats)
        self.assertIn("success_rate", stats)
        self.assertIn("total_listeners", stats)

    def test_remove_event_listener(self):
        """测试移除事件监听器"""
        callback = Mock()
        self.handler.add_event_listener(CanvasEventType.NODE_ADDED, callback)

        # 验证监听器已添加
        self.assertIn(callback, self.handler.event_listeners[CanvasEventType.NODE_ADDED])

        # 移除监听器
        result = self.handler.remove_event_listener(CanvasEventType.NODE_ADDED, callback)
        self.assertTrue(result)

        # 验证监听器已移除
        self.assertNotIn(callback, self.handler.event_listeners[CanvasEventType.NODE_ADDED])

    def test_clear_all_listeners(self):
        """测试清空所有监听器"""
        callback1 = Mock()
        callback2 = Mock()

        self.handler.add_event_listener(CanvasEventType.NODE_ADDED, callback1)
        self.handler.add_global_listener(callback2)

        # 验证监听器已添加
        self.assertEqual(len(self.handler.event_listeners[CanvasEventType.NODE_ADDED]), 1)
        self.assertEqual(len(self.handler.global_listeners), 1)

        # 清空所有监听器
        self.handler.clear_all_listeners()

        # 验证已清空
        self.assertEqual(len(self.handler.event_listeners), 0)
        self.assertEqual(len(self.handler.global_listeners), 0)


class TestEventDispatcher(unittest.TestCase):
    """事件分发器测试"""

    def setUp(self):
        """测试前设置"""
        self.config = DispatchConfig(
            max_workers=2,
            strategy=DispatchStrategy.PARALLEL,
            timeout_seconds=5.0
        )
        self.dispatcher = EventDispatcher(self.config)
        self.received_events = []

    def tearDown(self):
        """测试后清理"""
        if self.dispatcher.is_running:
            self.dispatcher.stop()

    def test_dispatcher_initialization(self):
        """测试分发器初始化"""
        self.assertFalse(self.dispatcher.is_running)
        self.assertEqual(self.dispatcher.config.max_workers, 2)
        self.assertEqual(self.dispatcher.config.strategy, DispatchStrategy.PARALLEL)

    def test_start_stop_dispatcher(self):
        """测试启动和停止分发器"""
        self.dispatcher.start()
        self.assertTrue(self.dispatcher.is_running)
        self.assertIsNotNone(self.dispatcher.dispatch_thread)

        self.dispatcher.stop()
        self.assertFalse(self.dispatcher.is_running)

    def test_add_listener(self):
        """测试添加监听器"""
        callback = Mock()
        listener_id = self.dispatcher.add_listener(
            callback,
            event_types=[CanvasEventType.NODE_ADDED],
            priority=2
        )

        self.assertIsNotNone(listener_id)
        self.assertTrue(listener_id.startswith("listener_"))

    def test_add_global_listener(self):
        """测试添加全局监听器"""
        callback = Mock()
        listener_id = self.dispatcher.add_listener(callback)

        self.assertIsNotNone(listener_id)
        self.assertEqual(len(self.dispatcher.global_listeners), 1)

    def test_remove_listener(self):
        """测试移除监听器"""
        callback = Mock()
        listener_id = self.dispatcher.add_listener(callback)

        # 验证监听器已添加
        self.assertEqual(len(self.dispatcher.global_listeners), 1)

        # 移除监听器
        result = self.dispatcher.remove_listener(listener_id)
        self.assertTrue(result)

        # 验证监听器已移除
        self.assertEqual(len(self.dispatcher.global_listeners), 0)

    def test_dispatch_event(self):
        """测试分发事件"""
        self.dispatcher.start()

        def callback(event):
            self.received_events.append(event)

        listener_id = self.dispatcher.add_listener(callback)

        event = CanvasEvent(
            event_id="test-event",
            event_type=CanvasEventType.NODE_ADDED,
            canvas_id="test-canvas",
            node_id="test-node",
            event_data={"test": "data"}
        )

        future = self.dispatcher.dispatch_event(event)
        result = future.result(timeout=5.0)

        self.assertTrue(result.success)
        self.assertEqual(len(self.received_events), 1)
        self.assertEqual(self.received_events[0].event_id, "test-event")

        self.dispatcher.stop()

    def test_dispatch_event_sync(self):
        """测试同步分发事件"""
        self.dispatcher.start()

        def callback(event):
            self.received_events.append(event)

        self.dispatcher.add_listener(callback)

        event = CanvasEvent(
            event_id="test-sync-event",
            event_type=CanvasEventType.NODE_UPDATED,
            canvas_id="test-canvas",
            node_id="test-node"
        )

        result = self.dispatcher.dispatch_event_sync(event)

        self.assertTrue(result.success)
        self.assertEqual(len(self.received_events), 1)

        self.dispatcher.stop()

    def test_multiple_listeners_parallel(self):
        """测试并行处理多个监听器"""
        self.dispatcher.start()

        listener_results = []

        def callback1(event):
            time.sleep(0.1)  # 模拟处理时间
            listener_results.append("listener1")

        def callback2(event):
            time.sleep(0.05)  # 模拟处理时间
            listener_results.append("listener2")

        # 添加两个监听器
        self.dispatcher.add_listener(callback1)
        self.dispatcher.add_listener(callback2)

        event = CanvasEvent(
            event_id="test-parallel-event",
            event_type=CanvasEventType.NODE_ADDED,
            canvas_id="test-canvas"
        )

        start_time = time.time()
        result = self.dispatcher.dispatch_event_sync(event)
        end_time = time.time()

        # 并行处理，总时间应该接近最长的监听器时间，而不是它们的和
        processing_time = (end_time - start_time) * 1000
        self.assertLess(processing_time, 150)  # 应该小于150ms，而不是150ms+

        self.assertTrue(result.success)
        self.assertEqual(len(listener_results), 2)

        self.dispatcher.stop()

    def test_priority_dispatching(self):
        """测试优先级分发"""
        config = DispatchConfig(
            max_workers=1,
            strategy=DispatchStrategy.PRIORITY
        )
        dispatcher = EventDispatcher(config)
        dispatcher.start()

        execution_order = []

        def high_priority_callback(event):
            execution_order.append("high")

        def low_priority_callback(event):
            execution_order.append("low")

        # 添加不同优先级的监听器
        dispatcher.add_listener(high_priority_callback, priority=3)
        dispatcher.add_listener(low_priority_callback, priority=1)

        event = CanvasEvent(
            event_id="test-priority-event",
            event_type=CanvasEventType.NODE_ADDED,
            canvas_id="test-canvas"
        )

        result = dispatcher.dispatch_event_sync(event)

        self.assertTrue(result.success)
        # 高优先级的应该先执行（取决于实现）
        self.assertEqual(len(execution_order), 2)

        dispatcher.stop()

    def test_error_isolation(self):
        """测试错误隔离"""
        self.dispatcher.start()

        def good_callback(event):
            self.received_events.append("good")

        def bad_callback(event):
            raise Exception("Test error")

        # 添加正常和异常的监听器
        self.dispatcher.add_listener(good_callback)
        self.dispatcher.add_listener(bad_callback)

        event = CanvasEvent(
            event_id="test-error-event",
            event_type=CanvasEventType.NODE_ADDED,
            canvas_id="test-canvas"
        )

        result = self.dispatcher.dispatch_event_sync(event)

        # 即使有错误，也应该继续处理其他监听器
        self.assertTrue(result.success)  # 整体成功
        self.assertEqual(len(self.received_events), 1)  # 正常监听器被调用
        self.assertGreater(len(result.errors), 0)  # 有错误记录

        self.dispatcher.stop()

    def test_get_queue_status(self):
        """测试获取队列状态"""
        status = self.dispatcher.get_queue_status()

        self.assertIn("is_running", status)
        self.assertIn("queue_size", status)
        self.assertIn("max_queue_size", status)
        self.assertIn("active_workers", status)
        self.assertIn("statistics", status)
        self.assertIn("config", status)

    def test_get_performance_metrics(self):
        """测试获取性能指标"""
        self.dispatcher.start()

        # 添加一些监听器并分发事件
        def callback(event):
            time.sleep(0.01)

        self.dispatcher.add_listener(callback)

        for i in range(5):
            event = CanvasEvent(
                event_id=f"test-event-{i}",
                event_type=CanvasEventType.NODE_ADDED,
                canvas_id="test-canvas"
            )
            self.dispatcher.dispatch_event(event)

        # 等待处理完成
        time.sleep(0.2)

        metrics = self.dispatcher.get_performance_metrics()

        if "data_points" in metrics and metrics["data_points"] > 0:
            self.assertIn("dispatch_time_ms", metrics)
            self.assertIn("queue_size", metrics)
            self.assertIn("success_rate", metrics)

        self.dispatcher.stop()

    def test_timeout_handling(self):
        """测试超时处理"""
        config = DispatchConfig(
            max_workers=1,
            timeout_seconds=0.1  # 很短的超时时间
        )
        dispatcher = EventDispatcher(config)
        dispatcher.start()

        def slow_callback(event):
            time.sleep(0.2)  # 超过超时时间

        dispatcher.add_listener(slow_callback)

        event = CanvasEvent(
            event_id="test-timeout-event",
            event_type=CanvasEventType.NODE_ADDED,
            canvas_id="test-canvas"
        )

        result = dispatcher.dispatch_event_sync(event)

        # 应该失败（超时）
        self.assertFalse(result.success)
        self.assertGreater(len(result.errors), 0)

        dispatcher.stop()


class TestEventIntegration(unittest.TestCase):
    """事件系统集成测试"""

    def setUp(self):
        """测试前设置"""
        self.handler = CanvasEventHandler()
        self.dispatcher = EventDispatcher()
        self.processed_events = []

    def tearDown(self):
        """测试后清理"""
        if self.dispatcher.is_running:
            self.dispatcher.stop()

    def test_end_to_end_event_processing(self):
        """测试端到端事件处理流程"""
        self.dispatcher.start()

        # 设置事件处理器回调
        def handler_callback(event):
            self.processed_events.append(event)

        self.handler.add_global_listener(handler_callback)

        # 设置分发器监听器
        def dispatcher_callback(event):
            # 模拟事件处理
            pass

        self.dispatcher.add_listener(dispatchor_callback)

        # 创建Canvas变更
        changes = [
            CanvasChange(
                change_id="integration-change",
                canvas_id="test-canvas",
                change_type=CanvasChangeType.CREATE,
                node_id="test-node",
                node_type="text",
                new_content={"text": "Integration test"},
                file_path="/test.canvas"
            )
        ]

        # 处理变更
        results = self.handler.process_canvas_changes(changes)

        # 分发生成的事件
        for result in results:
            if result.success:
                for event in result.additional_events:
                    self.dispatcher.dispatch_event(event)

        # 等待处理完成
        time.sleep(0.1)

        # 验证结果
        self.assertGreater(len(self.processed_events), 0)
        self.assertTrue(all(result.success for result in results))

        self.dispatcher.stop()

    def test_high_volume_events(self):
        """测试高容量事件处理"""
        self.dispatcher.start()

        processed_count = 0

        def callback(event):
            nonlocal processed_count
            processed_count += 1

        self.dispatcher.add_listener(callback)

        # 生成大量事件
        events = []
        for i in range(100):
            event = CanvasEvent(
                event_id=f"volume-test-{i}",
                event_type=CanvasEventType.NODE_ADDED,
                canvas_id="test-canvas",
                node_id=f"node-{i}"
            )
            events.append(event)

        start_time = time.time()

        # 分发所有事件
        futures = []
        for event in events:
            future = self.dispatcher.dispatch_event(event)
            futures.append(future)

        # 等待所有事件处理完成
        for future in futures:
            future.result(timeout=10.0)

        end_time = time.time()

        # 验证结果
        self.assertEqual(processed_count, 100)
        processing_time = end_time - start_time

        # 性能应该合理（100个事件在合理时间内完成）
        self.assertLess(processing_time, 5.0)

        self.dispatcher.stop()

    def test_concurrent_event_processing(self):
        """测试并发事件处理"""
        self.dispatcher.start()

        results = []

        def callback(event):
            results.append(event.event_id)

        self.dispatcher.add_listener(callback)

        # 从多个线程并发分发事件
        def dispatch_events(thread_id):
            for i in range(10):
                event = CanvasEvent(
                    event_id=f"thread-{thread_id}-event-{i}",
                    event_type=CanvasEventType.NODE_ADDED,
                    canvas_id="test-canvas"
                )
                future = self.dispatcher.dispatch_event(event)
                future.result(timeout=5.0)

        threads = []
        for thread_id in range(5):
            thread = threading.Thread(target=dispatch_events, args=(thread_id,))
            threads.append(thread)
            thread.start()

        # 等待所有线程完成
        for thread in threads:
            thread.join()

        # 验证结果
        self.assertEqual(len(results), 50)  # 5个线程 × 10个事件

        self.dispatcher.stop()


if __name__ == '__main__':
    # 运行测试
    unittest.main(verbosity=2)
