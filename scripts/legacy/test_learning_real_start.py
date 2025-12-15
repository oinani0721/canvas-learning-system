#!/usr/bin/env python3
"""
测试 /learning start 命令的真实启动功能
验证三个记忆系统的真实初始化：
1. Graphiti知识图谱 (DirectGraphitiStorage)
2. 时序记忆管理器 (TemporalMemoryManager)
3. 语义记忆管理器 (SemanticMemoryManager)
"""

import sys
import asyncio
import os
from pathlib import Path
from datetime import datetime
import json

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))


async def test_learning_start_with_monitoring():
    """测试 /learning start 命令的真实启动（带监控模式）"""

    print("=" * 70)
    print("[TEST] /learning start - Real Startup Verification")
    print("=" * 70)

    # Step 1: 导入LearningSessionManager
    print("\n[1] 导入LearningSessionManager...")
    try:
        from command_handlers.learning_commands import LearningSessionManager
        print("    [OK] 模块导入成功")
    except ImportError as e:
        print(f"    [FAIL] 模块导入失败: {e}")
        return False

    # Step 2: 准备测试Canvas
    print("\n[2] 准备测试Canvas...")
    canvas_path = "tests/fixtures/test-basic.canvas"

    if not os.path.exists(canvas_path):
        print(f"    [FAIL] Canvas文件不存在: {canvas_path}")
        return False

    print(f"    [OK] Canvas文件存在: {canvas_path}")

    # Step 3: 创建LearningSessionManager实例
    print("\n[3] 创建LearningSessionManager实例...")
    try:
        session_dir = ".learning_sessions"
        manager = LearningSessionManager(session_dir=session_dir)
        print(f"    [OK] Manager创建成功，会话目录: {session_dir}")
    except Exception as e:
        print(f"    [FAIL] Manager创建失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Step 4: 启动学习会话
    print("\n[4] 启动学习会话...")
    print("    注意: 这将真实初始化三个记忆系统")
    print("    - Graphiti知识图谱 (DirectGraphitiStorage)")
    print("    - 时序记忆管理器 (TemporalMemoryManager)")
    print("    - 语义记忆管理器 (SemanticMemoryManager)")
    print()

    try:
        result = await manager.start_session(
            canvas_path=canvas_path,
            user_id="test_user",
            session_name="测试学习会话 - 真实启动验证"
        )

        print(f"    [OK] 会话启动命令执行完成")
        print(f"    会话ID: {result.get('session_id')}")
        print(f"    会话文件: {result.get('session_file')}")

    except Exception as e:
        print(f"    [FAIL] 会话启动失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Step 5: 验证记忆系统状态
    print("\n[5] 验证记忆系统真实状态...")

    memory_systems = result.get('memory_systems', {})

    systems_info = []

    # 检查Graphiti
    graphiti_status = memory_systems.get('graphiti', {})
    graphiti_running = graphiti_status.get('status') == 'running'

    if graphiti_running:
        print(f"    [OK] Graphiti知识图谱: 运行中")
        print(f"        Memory ID: {graphiti_status.get('memory_id')}")
        print(f"        存储位置: {graphiti_status.get('storage')}")
        print(f"        初始化时间: {graphiti_status.get('initialized_at')}")
        systems_info.append('Graphiti')
    else:
        print(f"    [WARNING] Graphiti知识图谱: 不可用")
        print(f"        原因: {graphiti_status.get('error', 'Unknown')}")
        print(f"        尝试时间: {graphiti_status.get('attempted_at')}")

    # 检查Temporal
    temporal_status = memory_systems.get('temporal', {})
    temporal_running = temporal_status.get('status') == 'running'

    if temporal_running:
        print(f"    [OK] 时序记忆管理器: 运行中")
        print(f"        Session ID: {temporal_status.get('session_id')}")
        print(f"        存储位置: {temporal_status.get('storage')}")
        print(f"        初始化时间: {temporal_status.get('initialized_at')}")
        systems_info.append('Temporal')
    else:
        print(f"    [WARNING] 时序记忆管理器: 不可用")
        print(f"        原因: {temporal_status.get('error', 'Unknown')}")
        print(f"        尝试时间: {temporal_status.get('attempted_at')}")

    # 检查Semantic
    semantic_status = memory_systems.get('semantic', {})
    semantic_running = semantic_status.get('status') == 'running'

    if semantic_running:
        print(f"    [OK] 语义记忆管理器: 运行中")
        print(f"        Memory ID: {semantic_status.get('memory_id')}")
        print(f"        存储位置: {semantic_status.get('storage')}")
        print(f"        初始化时间: {semantic_status.get('initialized_at')}")
        systems_info.append('Semantic')
    else:
        print(f"    [WARNING] 语义记忆管理器: 不可用")
        print(f"        原因: {semantic_status.get('error', 'Unknown')}")
        print(f"        尝试时间: {semantic_status.get('attempted_at')}")

    # Step 6: 验证会话JSON文件
    print("\n[6] 验证会话JSON文件...")
    session_file = result.get('session_file')

    if not session_file or not os.path.exists(session_file):
        print(f"    [FAIL] 会话文件不存在: {session_file}")
        return False

    print(f"    [OK] 会话文件存在: {session_file}")

    try:
        with open(session_file, 'r', encoding='utf-8') as f:
            session_data = json.load(f)

        print(f"    [OK] 会话JSON解析成功")
        print(f"    会话ID: {session_data.get('session_id')}")
        print(f"    会话名称: {session_data.get('session_name')}")
        print(f"    Canvas路径: {session_data.get('canvas_path')}")
        print(f"    启动时间: {session_data.get('start_time')}")

        # 验证记忆系统记录的真实性
        stored_systems = session_data.get('memory_systems', {})

        # 检查是否有真实的时间戳和ID
        for system_name, system_data in stored_systems.items():
            status = system_data.get('status')
            if status == 'running':
                has_init_time = 'initialized_at' in system_data
                has_system_id = any(key in system_data for key in ['memory_id', 'session_id', 'session_record_id'])

                if has_init_time and has_system_id:
                    print(f"    [VERIFIED] {system_name}: 真实启动记录存在")
                else:
                    print(f"    [WARNING] {system_name}: 缺少真实启动证据")
            elif status == 'unavailable':
                has_attempt_time = 'attempted_at' in system_data
                has_error = 'error' in system_data

                if has_attempt_time and has_error:
                    print(f"    [VERIFIED] {system_name}: 真实失败记录存在")
                else:
                    print(f"    [WARNING] {system_name}: 缺少失败详情")

    except Exception as e:
        print(f"    [FAIL] 会话JSON读取失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Step 7: 统计结果
    print("\n[7] 测试结果统计...")

    total_systems = 3
    running_systems = len(systems_info)

    print(f"    总记忆系统数: {total_systems}")
    print(f"    运行中系统: {running_systems}")
    print(f"    不可用系统: {total_systems - running_systems}")

    if running_systems > 0:
        print(f"    [OK] 至少有 {running_systems} 个记忆系统真实启动")

    if running_systems == 0:
        print(f"    [WARNING] 所有记忆系统不可用，但会话仍可创建")

    # 最终结果
    print("\n" + "=" * 70)
    if running_systems >= 1:
        print("[SUCCESS] /learning start 命令真实启动验证通过!")
        print("=" * 70)
        print(f"\n核心验证:")
        print(f"  [OK] LearningSessionManager正常工作")
        print(f"  [OK] 会话JSON文件正确生成")
        print(f"  [OK] 至少 {running_systems}/{total_systems} 记忆系统真实初始化")

        if running_systems == total_systems:
            print(f"  [PERFECT] 所有记忆系统都真实启动成功!")
        else:
            print(f"  [WARNING] 部分记忆系统不可用（优雅降级）")
            print(f"     运行中: {', '.join(systems_info)}")

        print(f"\n会话详情:")
        print(f"  会话ID: {result.get('session_id')}")
        print(f"  会话文件: {session_file}")
        print(f"  Canvas: {canvas_path}")

    else:
        print("[WARNING] 所有记忆系统不可用")
        print("=" * 70)
        print(f"\n注意:")
        print(f"  - 会话仍成功创建（优雅降级）")
        print(f"  - Canvas学习功能不受影响")
        print(f"  - 但学习历程不会被记录")
        print(f"\n建议:")
        print(f"  - 检查Neo4j是否运行")
        print(f"  - 检查MCP服务器状态")
        print(f"  - 查看错误日志获取详细信息")

    print()

    return running_systems >= 1


if __name__ == "__main__":
    try:
        success = asyncio.run(test_learning_start_with_monitoring())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n[INFO] 测试被用户中断")
        sys.exit(130)
    except Exception as e:
        print(f"\n[FATAL] 测试发生异常: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
