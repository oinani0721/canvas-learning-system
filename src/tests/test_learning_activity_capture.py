"""
学习活动捕获系统测试

测试学习活动实时捕获功能，包括：
- 活动捕获器基础功能
- Canvas事件监听
- 用户输入和行为记录
- Agent交互数据记录

Author: Canvas Learning System Team
Version: 1.0
Created: 2025-10-25
"""

import asyncio
import json
import os
import tempfile
import time
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pytest

# 导入被测试的模块
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from learning_activity_capture import (
    LearningActivity,
    SessionContext,
    LearningActivityCapture
)
from canvas_event_listener import (
    CanvasEventListener,
    CanvasEvent,
    CanvasEventDispatcher
)


class TestLearningActivity(unittest.TestCase):
    """测试学习活动数据模型"""

    def test_learning_activity_creation(self):
        """测试学习活动创建"""
        activity = LearningActivity(
            activity_type="node_interaction",
            user_id="test_user",
            canvas_path="test.canvas"
        )

        self.assertEqual(activity.activity_type, "node_interaction")
        self.assertEqual(activity.user_id, "test_user")
        self.assertEqual(activity.canvas_path, "test.canvas")
        self.assertIsInstance(activity.activity_id, str)
        self.assertIsInstance(activity.timestamp, datetime)

    def test_session_context_creation(self):
        """测试会话上下文创建"""
        session = SessionContext(
            user_id="test_user",
            canvas_path="test.canvas"
        )

        self.assertEqual(session.user_id, "test_user")
        self.assertEqual(session.canvas_path, "test.canvas")
        self.assertIsInstance(session.session_id, str)
        self.assertIsInstance(session.start_time, datetime)
        self.assertEqual(len(session.activities), 0)


class TestLearningActivityCapture(unittest.TestCase):
    """测试学习活动捕获器"""

    def setUp(self):
        """测试设置"""
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.temp_dir, "test_config.yaml")

        # 创建测试配置
        test_config = {
            'capture': {
                'enabled': True,
                'capture_frequency_ms': 100,
                'buffer_size_activities': 10,
                'auto_flush_interval_seconds': 1,
                'capture_scope': {
                    'node_interactions': True,
                    'text_inputs': True,
                    'agent_calls': True,
                    'scoring_results': True,
                    'canvas_navigation': True,
                    'time_spent': True
                }
            }
        }

        with open(self.config_path, 'w') as f:
            import yaml
            yaml.dump(test_config, f)

        self.capture = LearningActivityCapture(self.config_path)

    def tearDown(self):
        """测试清理"""
        self.capture.stop_capture()
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_capture_initialization(self):
        """测试捕获器初始化"""
        self.assertTrue(self.capture.config['capture']['enabled'])
        self.assertEqual(len(self.capture.active_sessions), 0)
        self.assertEqual(len(self.capture.activity_buffer), 0)
        self.assertFalse(self.capture.is_capturing)

    def test_start_stop_capture(self):
        """测试启动和停止捕获"""
        # 启动捕获
        result = self.capture.start_capture()
        self.assertTrue(result)
        self.assertTrue(self.capture.is_capturing)

        # 再次启动应该失败
        result = self.capture.start_capture()
        self.assertFalse(result)

        # 停止捕获
        result = self.capture.stop_capture()
        self.assertTrue(result)
        self.assertFalse(self.capture.is_capturing)

    def test_memory_session_management(self):
        """测试记忆会话管理"""
        # 启动捕获
        self.capture.start_capture()

        # 开始会话
        session_id = self.capture.start_memory_session("test_user", "test.canvas")
        self.assertIsInstance(session_id, str)
        self.assertIn(session_id, self.capture.active_sessions)

        # 获取活动会话
        active_sessions = self.capture.get_active_sessions()
        self.assertIn(session_id, active_sessions)

        # 结束会话
        result = self.capture.end_memory_session(session_id)
        self.assertTrue(result)
        self.assertNotIn(session_id, self.capture.active_sessions)

        # 结束不存在的会话应该失败
        result = self.capture.end_memory_session("nonexistent")
        self.assertFalse(result)

    def test_capture_node_interaction(self):
        """测试捕获节点交互"""
        self.capture.start_capture()

        activity_id = self.capture.capture_node_interaction(
            user_id="test_user",
            canvas_path="test.canvas",
            node_id="node_123",
            interaction_type="click",
            details={
                "reading_pattern": "sequential",
                "hesitation_indicators": ["long_pause"],
                "comprehension_signals": ["confusion_markers"]
            }
        )

        self.assertIsInstance(activity_id, str)
        self.assertGreater(len(activity_id), 0)
        self.assertEqual(len(self.capture.activity_buffer), 1)

    def test_capture_understanding_input(self):
        """测试捕获理解输入"""
        self.capture.start_capture()

        input_text = "这是一个测试输入，用来理解用户的想法和概念。"
        context = {
            "target_yellow_node": "yellow_456",
            "editing_pattern": "progressive_refinement",
            "edit_count": 3
        }

        activity_id = self.capture.capture_understanding_input(
            user_id="test_user",
            canvas_path="test.canvas",
            node_id="node_123",
            input_text=input_text,
            context=context
        )

        self.assertIsInstance(activity_id, str)
        self.assertEqual(len(self.capture.activity_buffer), 1)

        # 检查认知指标
        activity = self.capture.activity_buffer[0]
        self.assertIn("confidence_level", activity.cognitive_indicators)
        self.assertIn("conceptual_clarity", activity.cognitive_indicators)
        self.assertIn("example_usage_ability", activity.cognitive_indicators)
        self.assertIn("critical_thinking_engagement", activity.cognitive_indicators)

    def test_capture_agent_interaction(self):
        """测试捕获Agent交互"""
        self.capture.start_capture()

        interaction_data = {
            "request_context": "需要解释一个概念",
            "response_quality": "helpful",
            "time_spent_seconds": 120,
            "input_data": {"concept": "test"},
            "output_summary": "详细解释了概念",
            "user_satisfaction": "satisfied",
            "follow_up_actions": ["more_examples"]
        }

        activity_id = self.capture.capture_agent_interaction(
            user_id="test_user",
            canvas_path="test.canvas",
            agent_name="basic-decomposition",
            interaction_data=interaction_data
        )

        self.assertIsInstance(activity_id, str)
        self.assertEqual(len(self.capture.activity_buffer), 1)

    def test_capture_scoring_result(self):
        """测试捕获评分结果"""
        self.capture.start_capture()

        scoring_data = {
            "yellow_node_id": "yellow_456",
            "scores": {
                "accuracy": 18,
                "imagery": 15,
                "completeness": 12,
                "originality": 20
            },
            "total_score": 65,
            "color_transition": "red_to_purple",
            "recommendations": ["clarification-path", "memory-anchor"],
            "understanding_improvement": True,
            "remaining_gaps": ["formal_definition"],
            "next_learning_priority": "medium"
        }

        activity_id = self.capture.capture_scoring_result(
            user_id="test_user",
            canvas_path="test.canvas",
            scoring_data=scoring_data
        )

        self.assertIsInstance(activity_id, str)
        self.assertEqual(len(self.capture.activity_buffer), 1)

    def test_capture_learning_session_summary(self):
        """测试捕获学习会话总结"""
        self.capture.start_capture()

        session_data = {
            "canvas_path": "test.canvas",
            "duration_minutes": 45,
            "total_nodes_interacted": 8,
            "agents_used": ["basic-decomposition", "scoring-agent"],
            "learning_objectives_met": ["understand_concept"],
            "key_insights_gained": ["better_understanding"],
            "session_context": {"session_type": "review"}
        }

        activity_id = self.capture.capture_learning_session_summary(
            user_id="test_user",
            session_data=session_data
        )

        self.assertIsInstance(activity_id, str)
        self.assertEqual(len(self.capture.activity_buffer), 1)

    def test_buffer_flush(self):
        """测试缓冲区刷新"""
        # 设置小缓冲区以便测试
        self.capture.config['capture']['buffer_size_activities'] = 3
        self.capture.start_capture()

        # 添加超过缓冲区大小的活动
        for i in range(5):
            self.capture.capture_node_interaction(
                user_id="test_user",
                canvas_path="test.canvas",
                node_id=f"node_{i}",
                interaction_type="click",
                details={}
            )

        # 由于自动刷新，缓冲区应该被清空
        # 等待一下确保刷新完成
        time.sleep(0.5)
        self.assertEqual(len(self.capture.activity_buffer), 0)

    def test_capture_disabled_types(self):
        """测试禁用类型的捕获"""
        # 禁用节点交互捕获
        self.capture.config['capture']['capture_scope']['node_interactions'] = False
        self.capture.start_capture()

        activity_id = self.capture.capture_node_interaction(
            user_id="test_user",
            canvas_path="test.canvas",
            node_id="node_123",
            interaction_type="click",
            details={}
        )

        # 应该返回空字符串
        self.assertEqual(activity_id, "")
        self.assertEqual(len(self.capture.activity_buffer), 0)

    def test_confidence_estimation(self):
        """测试置信度估算"""
        self.capture.start_capture()

        # 测试短文本（低置信度）
        short_text = "测试"
        context = {"edit_count": 0}
        confidence = self.capture._estimate_confidence(short_text, context)
        self.assertLess(confidence, 0.6)

        # 测试长文本（高置信度）
        long_text = "这是一个很长很详细的测试文本，包含了很多详细的内容和解释，" \
                   "显示用户对这个概念有很深入的理解。"
        context = {"edit_count": 5}
        confidence = self.capture._estimate_confidence(long_text, context)
        self.assertGreater(confidence, 0.7)

    def test_buffer_status(self):
        """测试缓冲区状态"""
        status = self.capture.get_buffer_status()
        expected_keys = ["buffer_size", "active_sessions", "is_capturing", "config_enabled"]
        for key in expected_keys:
            self.assertIn(key, status)


class TestCanvasEventListener(unittest.TestCase):
    """测试Canvas事件监听器"""

    def setUp(self):
        """测试设置"""
        self.temp_dir = tempfile.mkdtemp()
        self.listener = CanvasEventListener()

    def tearDown(self):
        """测试清理"""
        self.listener.stop_listening()
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_listener_initialization(self):
        """测试监听器初始化"""
        self.assertFalse(self.listener.is_listening)
        self.assertEqual(len(self.listener.observers), 0)
        self.assertEqual(len(self.listener.canvas_states), 0)

    def test_start_stop_listening(self):
        """测试启动和停止监听"""
        # 创建测试Canvas目录
        test_canvas_dir = os.path.join(self.temp_dir, "test_canvases")
        os.makedirs(test_canvas_dir)

        # 启动监听
        result = self.listener.start_listening([test_canvas_dir])
        self.assertTrue(result)
        self.assertTrue(self.listener.is_listening)

        # 停止监听
        result = self.listener.stop_listening()
        self.assertTrue(result)
        self.assertFalse(self.listener.is_listening)

    def test_event_handler_registration(self):
        """测试事件处理器注册"""
        def test_handler(event):
            pass

        # 注册处理器
        self.listener.register_event_handler(test_handler)
        self.assertIn(test_handler, self.listener.event_handlers)

        # 注销处理器
        self.listener.unregister_event_handler(test_handler)
        self.assertNotIn(test_handler, self.listener.event_handlers)

    def test_listening_status(self):
        """测试监听状态"""
        status = self.listener.get_listening_status()
        expected_keys = ["is_listening", "watched_paths", "tracked_canvases", "event_handlers_count"]
        for key in expected_keys:
            self.assertIn(key, status)


class TestCanvasEventDispatcher(unittest.TestCase):
    """测试Canvas事件分发器"""

    def setUp(self):
        """测试设置"""
        self.dispatcher = CanvasEventDispatcher()

    def test_handler_registration(self):
        """测试处理器注册"""
        def test_handler(event):
            pass

        # 注册处理器
        self.dispatcher.register_handler(test_handler)
        self.assertIn(test_handler, self.dispatcher.handlers)

        # 注销处理器
        self.dispatcher.unregister_handler(test_handler)
        self.assertNotIn(test_handler, self.dispatcher.handlers)

    def test_event_dispatch(self):
        """测试事件分发"""
        events_received = []

        def test_handler(event):
            events_received.append(event)

        self.dispatcher.register_handler(test_handler)

        # 创建测试事件
        event = CanvasEvent(
            event_id="test_event",
            event_type="test",
            timestamp=datetime.now(),
            canvas_path="test.canvas",
            file_hash="test_hash",
            changes={},
            metadata={}
        )

        # 分发事件
        self.dispatcher.dispatch_event(event)

        # 等待异步处理
        time.sleep(0.5)

        # 验证事件被接收
        self.assertGreater(len(events_received), 0)


class TestIntegration(unittest.TestCase):
    """集成测试"""

    def setUp(self):
        """测试设置"""
        self.temp_dir = tempfile.mkdtemp()

        # 创建配置
        config_path = os.path.join(self.temp_dir, "test_config.yaml")
        test_config = {
            'capture': {
                'enabled': True,
                'capture_frequency_ms': 100,
                'buffer_size_activities': 10,
                'auto_flush_interval_seconds': 1,
                'capture_scope': {
                    'node_interactions': True,
                    'text_inputs': True,
                    'agent_calls': True,
                    'scoring_results': True,
                    'canvas_navigation': True,
                    'time_spent': True
                }
            }
        }

        with open(config_path, 'w') as f:
            import yaml
            yaml.dump(test_config, f)

        self.capture = LearningActivityCapture(config_path)
        self.listener = CanvasEventListener(self.capture)

    def tearDown(self):
        """测试清理"""
        self.listener.stop_listening()
        self.capture.stop_capture()
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_full_workflow(self):
        """测试完整工作流程"""
        # 启动捕获和监听
        self.capture.start_capture()

        # 开始会话
        session_id = self.capture.start_memory_session("test_user", "test.canvas")

        # 捕获各种活动
        self.capture.capture_node_interaction(
            user_id="test_user",
            canvas_path="test.canvas",
            node_id="node_1",
            interaction_type="click",
            details={}
        )

        self.capture.capture_understanding_input(
            user_id="test_user",
            canvas_path="test.canvas",
            node_id="node_1",
            input_text="用户的理解输入",
            context={}
        )

        # 结束会话
        self.capture.end_memory_session(session_id)

        # 验证活动被记录
        session_activities = self.capture.get_session_activities(session_id)
        self.assertGreater(len(session_activities), 0)


if __name__ == '__main__':
    # 运行测试
    unittest.main(verbosity=2)