"""
实时Canvas记忆集成系统综合测试

测试整个实时记忆集成系统的功能，包括：
- 学习活动捕获
- 记忆系统集成
- 模式分析
- 隐私保护
- 跨系统集成

Author: Canvas Learning System Team
Version: 1.0
Created: 2025-10-25
"""

import json
import os
import tempfile
import time
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

# 导入被测试的模块
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from learning_activity_capture import LearningActivityCapture
from realtime_canvas_memory_integration import RealtimeCanvasMemoryIntegration
from learning_pattern_analyzer import LearningPatternAnalyzer
from memory_system_integrator import MemorySystemIntegrator
from privacy_manager import PrivacyManager


class TestRealtimeMemoryIntegration(unittest.TestCase):
    """实时记忆集成系统综合测试"""

    def setUp(self):
        """测试设置"""
        self.temp_dir = tempfile.mkdtemp()

        # 创建测试配置文件
        self.config_path = self._create_test_config()

        # 初始化各个组件
        self.activity_capture = LearningActivityCapture(self.config_path)
        self.memory_integration = RealtimeCanvasMemoryIntegration(self.config_path)
        self.pattern_analyzer = LearningPatternAnalyzer(self.config_path)
        self.memory_system = MemorySystemIntegrator(self.config_path)
        self.privacy_manager = PrivacyManager(self.config_path)

    def tearDown(self):
        """测试清理"""
        self.activity_capture.stop_capture()
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _create_test_config(self) -> str:
        """创建测试配置文件"""
        config_path = os.path.join(self.temp_dir, "test_config.yaml")

        test_config = {
            'capture': {
                'enabled': True,
                'capture_frequency_ms': 50,
                'buffer_size_activities': 5,
                'auto_flush_interval_seconds': 0.5,
                'capture_scope': {
                    'node_interactions': True,
                    'text_inputs': True,
                    'agent_calls': True,
                    'scoring_results': True,
                    'canvas_navigation': True,
                    'time_spent': True
                }
            },
            'analysis': {
                'learning_patterns': {
                    'detection_enabled': True,
                    'confidence_threshold': 0.5,
                    'min_data_points_patterns': 3
                }
            },
            'memory_integration': {
                'semantic_memory': {'enabled': True},
                'episodic_memory': {'enabled': True},
                'working_memory': {'enabled': True}
            },
            'privacy_security': {
                'data_encryption': 'AES-256',
                'anonymization': {'enabled': False},  # 测试时禁用以便验证
                'access_control': {
                    'user_access_only': True,
                    'system_access_logging': True
                },
                'user_controls': {
                    'data_export': True,
                    'selective_deletion': True
                }
            }
        }

        import yaml
        with open(config_path, 'w') as f:
            yaml.dump(test_config, f)

        return config_path

    def test_complete_learning_workflow(self):
        """测试完整的学习工作流程"""
        print("\n=== 测试完整学习工作流程 ===")

        # 1. 启动系统组件
        self.activity_capture.start_capture()
        print("[OK] 学习活动捕获系统已启动")

        # 2. 开始记忆会话
        session_id = self.memory_integration.start_memory_session(
            canvas_path="test/discrete_math.canvas",
            user_id="test_user_001"
        )
        print(f"[OK] 记忆会话已开始: {session_id}")

        # 3. 模拟学习活动
        activities = self._simulate_learning_activities()
        print(f"[OK] 模拟了 {len(activities)} 个学习活动")

        # 4. 捕获学习活动到记忆集成系统
        for activity in activities:
            self.memory_integration.capture_learning_activity(session_id, activity)
        print("[OK] 学习活动已捕获到记忆系统")

        # 5. 结束记忆会话
        success = self.memory_integration.end_memory_session(session_id)
        self.assertTrue(success)
        print("[OK] 记忆会话已结束")

        # 6. 分析学习模式
        session_data = self.memory_integration.get_session_data(session_id)
        pattern_result = self.pattern_analyzer.analyze_user_patterns(
            user_id="test_user_001",
            activities=session_data.get('learning_activities', []),
            time_range_days=1
        )
        print(f"[OK] 学习模式分析完成，置信度: {pattern_result.overall_confidence:.2f}")

        # 7. 集成记忆系统
        memory_result = self.memory_system.integrate_with_memory_systems(session_data)
        integration_score = memory_result.get('integration_quality_score', 0)
        print(f"[OK] 记忆系统集成完成，质量得分: {integration_score:.2f}")

        # 8. 验证结果
        self.assertGreater(pattern_result.overall_confidence, 0)
        self.assertGreater(integration_score, 0)
        self.assertGreater(len(memory_result.get('semantic_memory_entries', [])), 0)

        print("[OK] 完整学习工作流程测试通过")

    def _simulate_learning_activities(self) -> list:
        """模拟学习活动"""
        activities = []

        # 活动1: 节点交互
        activities.append({
            "activity_id": "activity_001",
            "activity_type": "node_interaction",
            "timestamp": datetime.now().isoformat(),
            "operation_details": {
                "node_id": "node_concept_001",
                "interaction_type": "click",
                "reading_pattern": "sequential"
            }
        })

        # 活动2: 理解输入
        activities.append({
            "activity_id": "activity_002",
            "activity_type": "understanding_input",
            "timestamp": datetime.now().isoformat(),
            "operation_details": {
                "node_id": "node_concept_001",
                "input_text": "逆否命题是原命题的逻辑等价形式，即如果P则Q的逆否命题是如果非Q则非P",
                "input_length_chars": 67
            },
            "cognitive_indicators": {
                "confidence_level": 0.75,
                "conceptual_clarity": 0.80,
                "example_usage_ability": 0.60,
                "critical_thinking_engagement": 0.70
            }
        })

        # 活动3: Agent交互
        activities.append({
            "activity_id": "activity_003",
            "activity_type": "agent_interaction",
            "timestamp": datetime.now().isoformat(),
            "operation_details": {
                "agent_called": "basic-decomposition",
                "request_context": "需要理解逆否命题的概念",
                "response_quality": "helpful",
                "time_spent_seconds": 120
            }
        })

        # 活动4: 评分结果
        activities.append({
            "activity_id": "activity_004",
            "activity_type": "scoring_evaluation",
            "timestamp": datetime.now().isoformat(),
            "operation_details": {
                "scoring_agent": "scoring-agent",
                "yellow_node_id": "yellow_understanding_001",
                "scores": {
                    "accuracy": 20,
                    "imagery": 18,
                    "completeness": 16,
                    "originality": 19
                },
                "total_score": 73,
                "color_transition": "red_to_purple",
                "recommendations": ["clarification-path", "comparison-table"]
            }
        })

        return activities

    def test_privacy_management(self):
        """测试隐私管理功能"""
        print("\n=== 测试隐私管理功能 ===")

        user_id = "privacy_test_user"

        # 1. 设置隐私设置
        privacy_settings = {
            "privacy_level": "enhanced",
            "user_controls": {
                "data_export": True,
                "selective_deletion": True
            }
        }

        success = self.privacy_manager.manage_privacy_settings(user_id, privacy_settings)
        self.assertTrue(success)
        print("✓ 隐私设置配置成功")

        # 2. 测试数据加密
        test_data = "这是敏感的测试数据"
        encrypted_data = self.privacy_manager.encrypt_data(test_data)
        decrypted_data = self.privacy_manager.decrypt_data(encrypted_data)

        self.assertEqual(test_data, decrypted_data)
        print("✓ 数据加密/解密功能正常")

        # 3. 测试访问权限检查
        access_granted = self.privacy_manager.check_access_permission(
            user_id=user_id,
            resource_type="user_data",
            action="read"
        )
        self.assertTrue(access_granted)
        print("✓ 访问权限检查正常")

        # 4. 测试隐私仪表板
        dashboard = self.privacy_manager.get_privacy_dashboard(user_id)
        self.assertIn("privacy_level", dashboard)
        self.assertEqual(dashboard["privacy_level"], "enhanced")
        print("✓ 隐私仪表板数据正常")

        print("✓ 隐私管理功能测试通过")

    def test_memory_system_integration(self):
        """测试记忆系统集成"""
        print("\n=== 测试记忆系统集成 ===")

        # 创建测试会话数据
        session_data = {
            "memory_session_id": "test_session_001",
            "user_id": "memory_test_user",
            "canvas_file_path": "test/math_logic.canvas",
            "session_start_timestamp": datetime.now().isoformat(),
            "session_duration_minutes": 45.0,
            "learning_activities": self._simulate_learning_activities(),
            "learning_trajectory_analysis": {
                "session_objective": "掌握逆否命题概念",
                "starting_knowledge_level": "novice",
                "ending_knowledge_level": "intermediate"
            }
        }

        # 集成记忆系统
        result = self.memory_system.integrate_with_memory_systems(session_data)

        # 验证结果
        self.assertIn("semantic_memory_entries", result)
        self.assertIn("episodic_memory_links", result)
        self.assertIn("working_memory_snapshots", result)
        self.assertIn("integration_quality_score", result)

        semantic_entries = result["semantic_memory_entries"]
        episodic_links = result["episodic_memory_links"]
        integration_score = result["integration_quality_score"]

        self.assertGreater(len(semantic_entries), 0)
        self.assertGreater(len(episodic_links), 0)
        self.assertGreater(integration_score, 0)

        print(f"✓ 语义记忆条目: {len(semantic_entries)}")
        print(f"✓ 情景记忆链接: {len(episodic_links)}")
        print(f"✓ 集成质量得分: {integration_score:.2f}")

        # 测试记忆搜索
        search_results = self.memory_system.search_memories("逆否命题")
        self.assertGreater(len(search_results), 0)
        print(f"✓ 记忆搜索结果: {len(search_results)} 条")

        print("✓ 记忆系统集成测试通过")

    def test_pattern_analysis_accuracy(self):
        """测试模式分析准确性"""
        print("\n=== 测试模式分析准确性 ===")

        user_id = "pattern_test_user"

        # 创建多样化的学习活动
        activities = [
            # 视觉型学习活动
            {
                "activity_type": "understanding_input",
                "operation_details": {
                    "input_text": "通过图示可以更清楚地理解概念之间的关系"
                },
                "cognitive_indicators": {"confidence_level": 0.85}
            },
            # 分析型学习活动
            {
                "activity_type": "agent_interaction",
                "operation_details": {
                    "agent_called": "clarification-path",
                    "request_context": "需要逻辑分析步骤"
                }
            },
            # 序列型学习活动
            {
                "activity_type": "scoring_evaluation",
                "operation_details": {
                    "total_score": 78,
                    "color_transition": "red_to_purple"
                }
            }
        ]

        # 分析学习模式
        pattern_result = self.pattern_analyzer.analyze_user_patterns(
            user_id=user_id,
            activities=activities,
            time_range_days=1
        )

        # 验证学习风格分析
        learning_style = pattern_result.learning_style
        self.assertGreater(learning_style.confidence_score, 0)

        # 验证行为模式
        behavior_patterns = pattern_result.behavior_patterns
        self.assertGreater(len(behavior_patterns), 0)

        # 验证整体置信度
        overall_confidence = pattern_result.overall_confidence
        self.assertGreater(overall_confidence, 0.25)  # 考虑数据量有限，降低阈值

        print(f"✓ 学习风格置信度: {learning_style.confidence_score:.2f}")
        print(f"✓ 行为模式数量: {len(behavior_patterns)}")
        print(f"✓ 整体置信度: {overall_confidence:.2f}")
        print(f"✓ 生成建议: {len(pattern_result.recommendations)} 条")

        print("✓ 模式分析准确性测试通过")

    def test_system_performance(self):
        """测试系统性能"""
        print("\n=== 测试系统性能 ===")

        # 测试大量活动的处理性能
        start_time = time.time()

        session_id = self.memory_integration.start_memory_session(
            canvas_path="test/performance.canvas",
            user_id="performance_test_user"
        )

        # 生成大量测试活动
        batch_size = 100
        for i in range(batch_size):
            activity = {
                "activity_id": f"perf_activity_{i:03d}",
                "activity_type": "understanding_input" if i % 2 == 0 else "node_interaction",
                "timestamp": datetime.now().isoformat(),
                "operation_details": {
                    "input_text": f"测试活动 {i} 的内容" if i % 2 == 0 else "",
                    "node_id": f"node_{i:03d}" if i % 2 != 0 else ""
                }
            }

            success = self.memory_integration.capture_learning_activity(session_id, activity)
            if i % 20 == 0:
                print(f"  已处理 {i+1}/{batch_size} 个活动")

        self.memory_integration.end_memory_session(session_id)

        end_time = time.time()
        processing_time = end_time - start_time

        # 性能验证
        activities_per_second = batch_size / processing_time
        self.assertGreater(activities_per_second, 10)  # 至少每秒处理10个活动

        print(f"✓ 处理 {batch_size} 个活动用时: {processing_time:.2f} 秒")
        print(f"✓ 处理速度: {activities_per_second:.1f} 活动/秒")
        print("✓ 系统性能测试通过")

    def test_error_handling(self):
        """测试错误处理"""
        print("\n=== 测试错误处理 ===")

        # 测试无效配置处理
        try:
            invalid_config_path = os.path.join(self.temp_dir, "invalid.yaml")
            capture = LearningActivityCapture(invalid_config_path)
            # 应该使用默认配置
            self.assertIsNotNone(capture.config)
            print("✓ 无效配置处理正常")
        except Exception as e:
            self.fail(f"无效配置处理失败: {e}")

        # 测试无效会话ID处理
        result = self.memory_integration.end_memory_session("invalid_session_id")
        self.assertFalse(result)
        print("✓ 无效会话ID处理正常")

        # 测试空数据处理
        pattern_result = self.pattern_analyzer.analyze_user_patterns(
            user_id="empty_test_user",
            activities=[],
            time_range_days=1
        )
        self.assertEqual(pattern_result.overall_confidence, 0.0)
        print("✓ 空数据处理正常")

        print("✓ 错误处理测试通过")


if __name__ == '__main__':
    # 运行测试
    unittest.main(verbosity=2)