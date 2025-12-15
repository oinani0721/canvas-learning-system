#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
启动Canvas学习会话
临时启动脚本
"""

import sys
import os
from datetime import datetime
from pathlib import Path

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def start_learning_session_async():
    """启动学习会话（异步）"""

    # 配置UTF-8输出
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    try:
        from learning_session_wrapper import LearningSessionWrapper

        # 创建学习会话包装器
        wrapper = LearningSessionWrapper()

        # Canvas文件路径
        canvas_path = "笔记库/Canvas/CS70/CS70HW1/CS70 Lecture1.canvas"

        # 检查文件是否存在
        full_path = Path(canvas_path)
        if not full_path.exists():
            print(f"[ERROR] Canvas file not found: {canvas_path}")
            return False

        print("=" * 60)
        print("Canvas Learning Session Starting...")
        print("=" * 60)
        print(f"Canvas: {canvas_path}")
        print(f"User: default")
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)

        # 启动会话（异步调用）
        result = await wrapper.start_session(
            canvas_path=canvas_path,
            user_id="default",
            session_name="CS70 Lecture1 Learning Session"
        )

        if result and result.get('success'):
            print("\n[SUCCESS] Learning session started!")
            print(f"Session ID: {result['session_id']}")
            print(f"Session Name: {result['session_name']}")
            print()
            print("Enabled Memory Systems:")
            for system_name, enabled in result['memory_systems'].items():
                status = "[ON]" if enabled else "[OFF]"
                print(f"  {status} {system_name}")
            print()
            print("=" * 60)
            print("Tips:")
            print("  - Canvas file monitoring is running in background")
            print("  - All your learning activities will be recorded")
            print("  - Use /learning status to check session status")
            print("  - Use /learning stop to end session and generate report")
            print("=" * 60)

            return True
        else:
            error_msg = result.get('error', 'Unknown error') if result else 'No result returned'
            print(f"\n[ERROR] Failed to start learning session: {error_msg}")
            return False

    except Exception as e:
        print(f"\n[ERROR] Startup failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def start_learning_session():
    """启动学习会话（同步包装）"""
    import asyncio
    try:
        return asyncio.run(start_learning_session_async())
    except Exception as e:
        print(f"[ERROR] Async execution failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = start_learning_session()
    sys.exit(0 if success else 1)
