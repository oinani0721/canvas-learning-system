#!/usr/bin/env python3
"""
实时Canvas记忆集成系统演示

演示完整的实时记忆集成系统功能，包括：
1. 学习活动实时捕获
2. 记忆会话管理
3. 学习模式分析
4. 记忆系统集成
5. 隐私保护

Usage: python demo_realtime_memory_system.py
"""

import os
import sys
import time
import tempfile
from datetime import datetime

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from learning_activity_capture import LearningActivityCapture
from realtime_canvas_memory_integration import RealtimeCanvasMemoryIntegration
from learning_pattern_analyzer import LearningPatternAnalyzer
from memory_system_integrator import MemorySystemIntegrator
from privacy_manager import PrivacyManager


def create_demo_config():
    """创建演示配置"""
    import yaml

    config = {
        'capture': {
            'enabled': True,
            'capture_frequency_ms': 100,
            'buffer_size_activities': 10,
            'auto_flush_interval_seconds': 2,
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
            'anonymization': {'enabled': False},  # 演示时禁用以便观察
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

    temp_dir = tempfile.mkdtemp()
    config_path = os.path.join(temp_dir, "demo_config.yaml")

    with open(config_path, 'w') as f:
        yaml.dump(config, f)

    return config_path, temp_dir


def simulate_learning_session():
    """模拟学习会话"""
    print("\n[START] 启动实时Canvas记忆集成系统演示")

    # 创建配置
    config_path, temp_dir = create_demo_config()

    try:
        # 初始化系统组件
        print("\n📋 初始化系统组件...")
        activity_capture = LearningActivityCapture(config_path)
        memory_integration = RealtimeCanvasMemoryIntegration(config_path)
        pattern_analyzer = LearningPatternAnalyzer(config_path)
        memory_system = MemorySystemIntegrator(config_path)
        privacy_manager = PrivacyManager(config_path)

        print("✅ 所有系统组件初始化完成")

        # 启动活动捕获
        print("\n🎯 启动学习活动实时捕获...")
        activity_capture.start_capture()

        # 开始学习会话
        print("\n📚 开始学习会话：学习'逆否命题'概念")
        session_id = memory_integration.start_memory_session(
            canvas_path="demo/discrete_math.canvas",
            user_id="demo_user"
        )
        print(f"会话ID: {session_id}")

        # 模拟学习活动序列
        print("\n🧠 模拟学习活动序列...")

        # 活动1: 首次接触概念（不理解）
        activity1 = {
            "activity_id": "demo_activity_001",
            "activity_type": "node_interaction",
            "timestamp": datetime.now().isoformat(),
            "operation_details": {
                "node_id": "node_converse_proposition",
                "interaction_type": "click",
                "reading_pattern": "confused_reading",
                "hesitation_indicators": ["repeated_reading", "long_pause"]
            }
        }
        memory_integration.capture_learning_activity(session_id, activity1)
        print("1. 用户点击'逆否命题'节点，表现出困惑")

        time.sleep(0.5)

        # 活动2: 请求基础拆解
        activity2 = {
            "activity_id": "demo_activity_002",
            "activity_type": "agent_interaction",
            "timestamp": datetime.now().isoformat(),
            "operation_details": {
                "agent_called": "basic-decomposition",
                "request_context": "完全不理解什么是逆否命题，需要从基础开始",
                "response_quality": "helpful",
                "time_spent_seconds": 180
            }
        }
        memory_integration.capture_learning_activity(session_id, activity2)
        print("2. 用户调用basic-decomposition agent获得基础解释")

        time.sleep(0.5)

        # 活动3: 输入初步理解
        activity3 = {
            "activity_id": "demo_activity_003",
            "activity_type": "understanding_input",
            "timestamp": datetime.now().isoformat(),
            "operation_details": {
                "node_id": "node_converse_proposition",
                "input_text": "逆否命题就是把原来的命题反过来然后否定，比如如果P则Q，逆否命题就是如果非Q则非P",
                "input_length_chars": 67,
                "editing_pattern": "progressive_refinement"
            },
            "cognitive_indicators": {
                "confidence_level": 0.65,
                "conceptual_clarity": 0.58,
                "example_usage_ability": 0.42,
                "critical_thinking_engagement": 0.71
            }
        }
        memory_integration.capture_learning_activity(session_id, activity3)
        print("3. 用户输入初步理解，显示部分掌握")

        time.sleep(0.5)

        # 活动4: 评分结果（紫色，似懂非懂）
        activity4 = {
            "activity_id": "demo_activity_004",
            "activity_type": "scoring_evaluation",
            "timestamp": datetime.now().isoformat(),
            "operation_details": {
                "scoring_agent": "scoring-agent",
                "yellow_node_id": "yellow_understanding_001",
                "scores": {
                    "accuracy": 18,
                    "imagery": 15,
                    "completeness": 12,
                    "originality": 20
                },
                "total_score": 65,
                "color_transition": "red_to_purple",
                "recommendations": ["clarification-path", "comparison-table"]
            },
            "impact_analysis": {
                "understanding_improvement": True,
                "remaining_gaps": ["formal_definition", "practical_examples"],
                "next_learning_priority": "medium"
            }
        }
        memory_integration.capture_learning_activity(session_id, activity4)
        print("4. 评分结果：65分（紫色），需要进一步澄清")

        time.sleep(0.5)

        # 活动5: 深度澄清
        activity5 = {
            "activity_id": "demo_activity_005",
            "activity_type": "agent_interaction",
            "timestamp": datetime.now().isoformat(),
            "operation_details": {
                "agent_called": "clarification-path",
                "request_context": "需要更深入的理解逆否命题的逻辑等价性",
                "response_quality": "excellent",
                "time_spent_seconds": 300
            }
        }
        memory_integration.capture_learning_activity(session_id, activity5)
        print("5. 用户调用clarification-path agent进行深度学习")

        time.sleep(0.5)

        # 活动6: 评分结果（绿色，完全理解）
        activity6 = {
            "activity_id": "demo_activity_006",
            "activity_type": "scoring_evaluation",
            "timestamp": datetime.now().isoformat(),
            "operation_details": {
                "scoring_agent": "scoring-agent",
                "yellow_node_id": "yellow_understanding_002",
                "scores": {
                    "accuracy": 23,
                    "imagery": 21,
                    "completeness": 22,
                    "originality": 24
                },
                "total_score": 90,
                "color_transition": "purple_to_green",
                "recommendations": ["example-teaching"]
            }
        }
        memory_integration.capture_learning_activity(session_id, activity6)
        print("6. 最终评分：90分（绿色），完全理解概念")

        # 结束学习会话
        print("\n🏁 结束学习会话...")
        success = memory_integration.end_memory_session(session_id)
        print(f"会话结束成功: {success}")

        # 分析学习模式
        print("\n📊 分析学习模式...")
        session_data = memory_integration.get_session_data(session_id)
        pattern_result = pattern_analyzer.analyze_user_patterns(
            user_id="demo_user",
            activities=session_data.get('learning_activities', []),
            time_range_days=1
        )

        print(f"学习风格置信度: {pattern_result.learning_style.confidence_score:.2f}")
        print(f"整体置信度: {pattern_result.overall_confidence:.2f}")
        print(f"识别的行为模式: {len(pattern_result.behavior_patterns)}")
        print("学习建议:")
        for i, rec in enumerate(pattern_result.recommendations[:3], 1):
            print(f"  {i}. {rec}")

        # 集成记忆系统
        print("\n🧠 集成记忆系统...")
        memory_result = memory_system.integrate_with_memory_systems(session_data)
        integration_score = memory_result.get('integration_quality_score', 0)

        print(f"语义记忆条目: {len(memory_result.get('semantic_memory_entries', []))}")
        print(f"情景记忆链接: {len(memory_result.get('episodic_memory_links', []))}")
        print(f"工作记忆快照: {len(memory_result.get('working_memory_snapshots', []))}")
        print(f"集成质量得分: {integration_score:.2f}")

        # 隐私保护演示
        print("\n🔒 隐私保护功能演示...")
        privacy_settings = {
            "privacy_level": "enhanced",
            "user_controls": {
                "data_export": True,
                "selective_deletion": True
            }
        }
        privacy_manager.manage_privacy_settings("demo_user", privacy_settings)
        print("隐私设置配置完成")

        dashboard = privacy_manager.get_privacy_dashboard("demo_user")
        print(f"隐私级别: {dashboard['privacy_level']}")
        print(f"数据导出状态: {dashboard['data_export_status']}")

        # 数据加密演示
        test_data = "用户的学习隐私数据"
        encrypted = privacy_manager.encrypt_data(test_data)
        decrypted = privacy_manager.decrypt_data(encrypted)
        print(f"数据加密验证: {'成功' if test_data == decrypted else '失败'}")

        # 系统统计
        print("\n📈 系统统计信息...")
        print(f"活跃记忆会话: {len(memory_integration.get_active_sessions())}")
        buffer_status = activity_capture.get_buffer_status()
        print(f"活动缓冲区状态: {buffer_status['buffer_size']} 个活动")
        memory_stats = memory_system.get_memory_statistics()
        print(f"记忆系统统计:")
        print(f"  语义记忆: {memory_stats['semantic_memory_count']} 条")
        print(f"  情景记忆: {memory_stats['episodic_memory_count']} 条")
        print(f"  工作记忆快照: {memory_stats['working_memory_snapshots_count']} 条")

        print("\n✨ 实时Canvas记忆集成系统演示完成！")
        print("\n🎯 主要功能验证:")
        print("  ✅ 实时学习活动捕获")
        print("  ✅ 记忆会话管理")
        print("  ✅ 学习模式智能分析")
        print("  ✅ 多层次记忆系统集成")
        print("  ✅ 端到端隐私保护")
        print("  ✅ 性能监控和统计")

    finally:
        # 清理资源
        print("\n🧹 清理系统资源...")
        if 'activity_capture' in locals():
            activity_capture.stop_capture()

        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)
        print("资源清理完成")


if __name__ == "__main__":
    simulate_learning_session()