#!/usr/bin/env python3
"""
实时Canvas记忆集成系统演示（简化版）

演示完整的实时记忆集成系统功能
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


def main():
    """主演示函数"""
    print("\n=== 实时Canvas记忆集成系统演示 ===")

    # 创建临时配置
    import yaml
    temp_dir = tempfile.mkdtemp()
    config_path = os.path.join(temp_dir, "demo_config.yaml")

    config = {
        'capture': {
            'enabled': True,
            'capture_frequency_ms': 100,
            'buffer_size_activities': 5,
            'auto_flush_interval_seconds': 1,
            'capture_scope': {
                'node_interactions': True,
                'text_inputs': True,
                'agent_calls': True,
                'scoring_results': True
            }
        },
        'memory_integration': {
            'semantic_memory': {'enabled': True},
            'episodic_memory': {'enabled': True},
            'working_memory': {'enabled': True}
        },
        'privacy_security': {
            'anonymization': {'enabled': False}
        }
    }

    with open(config_path, 'w') as f:
        yaml.dump(config, f)

    try:
        # 初始化系统
        print("\n1. 初始化系统组件...")
        activity_capture = LearningActivityCapture(config_path)
        memory_integration = RealtimeCanvasMemoryIntegration(config_path)
        pattern_analyzer = LearningPatternAnalyzer(config_path)
        memory_system = MemorySystemIntegrator(config_path)
        privacy_manager = PrivacyManager(config_path)
        print("   [OK] 所有组件初始化完成")

        # 启动捕获
        print("\n2. 启动学习活动捕获...")
        activity_capture.start_capture()
        print("   [OK] 捕获系统已启动")

        # 开始学习会话
        print("\n3. 开始学习会话...")
        session_id = memory_integration.start_memory_session(
            canvas_path="demo/math.canvas",
            user_id="demo_user"
        )
        print(f"   会话ID: {session_id}")

        # 模拟学习活动
        print("\n4. 模拟学习活动...")

        activities = [
            {
                "activity_id": "act_001",
                "activity_type": "node_interaction",
                "timestamp": datetime.now().isoformat(),
                "operation_details": {
                    "node_id": "concept_001",
                    "interaction_type": "click"
                }
            },
            {
                "activity_id": "act_002",
                "activity_type": "understanding_input",
                "timestamp": datetime.now().isoformat(),
                "operation_details": {
                    "input_text": "这是我对概念的理解",
                    "input_length_chars": 11
                },
                "cognitive_indicators": {
                    "confidence_level": 0.75
                }
            },
            {
                "activity_id": "act_003",
                "activity_type": "scoring_evaluation",
                "timestamp": datetime.now().isoformat(),
                "operation_details": {
                    "total_score": 78,
                    "color_transition": "red_to_purple"
                }
            }
        ]

        for i, activity in enumerate(activities, 1):
            memory_integration.capture_learning_activity(session_id, activity)
            print(f"   活动 {i}: {activity['activity_type']}")
            time.sleep(0.2)

        # 结束会话
        print("\n5. 结束学习会话...")
        success = memory_integration.end_memory_session(session_id)
        print(f"   [OK] 会话结束: {success}")

        # 分析模式
        print("\n6. 分析学习模式...")
        session_data = memory_integration.get_session_data(session_id)
        pattern_result = pattern_analyzer.analyze_user_patterns(
            user_id="demo_user",
            activities=session_data.get('learning_activities', [])
        )
        print(f"   整体置信度: {pattern_result.overall_confidence:.2f}")
        print(f"   学习风格置信度: {pattern_result.learning_style.confidence_score:.2f}")

        # 记忆集成
        print("\n7. 集成记忆系统...")
        memory_result = memory_system.integrate_with_memory_systems(session_data)
        integration_score = memory_result.get('integration_quality_score', 0)
        print(f"   集成质量得分: {integration_score:.2f}")
        print(f"   语义记忆条目: {len(memory_result.get('semantic_memory_entries', []))}")
        print(f"   情景记忆链接: {len(memory_result.get('episodic_memory_links', []))}")

        # 隐私保护
        print("\n8. 隐私保护演示...")
        test_data = "敏感测试数据"
        encrypted = privacy_manager.encrypt_data(test_data)
        decrypted = privacy_manager.decrypt_data(encrypted)
        print(f"   数据加密测试: {'通过' if test_data == decrypted else '失败'}")

        # 系统统计
        print("\n9. 系统统计...")
        buffer_status = activity_capture.get_buffer_status()
        print(f"   活动缓冲区: {buffer_status['buffer_size']} 个活动")
        print(f"   活动会话: {len(memory_integration.get_active_sessions())} 个")

        print("\n=== 演示完成 ===")
        print("\n主要功能验证:")
        print("  [OK] 实时学习活动捕获")
        print("  [OK] 记忆会话管理")
        print("  [OK] 学习模式分析")
        print("  [OK] 记忆系统集成")
        print("  [OK] 隐私保护")

    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # 清理
        if 'activity_capture' in locals():
            activity_capture.stop_capture()
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    main()