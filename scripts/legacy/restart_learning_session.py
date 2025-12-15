#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
重新启动Canvas学习会话（修复后）
"""

import sys
import os

# ⚠️ CRITICAL: Load .env FIRST before any other imports
# This ensures environment variables are available when modules initialize
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("[INFO] Environment variables loaded from .env file")
except ImportError:
    print("[WARNING] python-dotenv not installed, using system environment variables")

# 验证Neo4j配置
neo4j_password = os.getenv('NEO4J_PASSWORD', 'not_set')
neo4j_uri = os.getenv('NEO4J_URI', 'not_set')
neo4j_user = os.getenv('NEO4J_USER', 'not_set')
print(f"[INFO] Neo4j URI: {neo4j_uri}")
print(f"[INFO] Neo4j User: {neo4j_user}")
print(f"[INFO] Neo4j Password: {'***' if neo4j_password != 'not_set' else 'NOT SET'}")

# NOW import other modules after .env is loaded
import io
from datetime import datetime
from pathlib import Path

# 配置UTF-8输出
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def restart_learning_session_async():
    """重新启动学习会话"""
    try:
        from learning_session_wrapper import LearningSessionWrapper

        print("=" * 60)
        print("Canvas Learning Session Restarting...")
        print("=" * 60)
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()

        # 创建学习会话包装器
        wrapper = LearningSessionWrapper()

        # Canvas文件路径
        canvas_path = "笔记库/Canvas/CS70/CS70HW1/CS70 Lecture1.canvas"

        # 检查文件是否存在
        full_path = Path(canvas_path)
        if not full_path.exists():
            print(f"[ERROR] Canvas file not found: {canvas_path}")
            return False

        print(f"Canvas: {canvas_path}")
        print(f"User: default")
        print("=" * 60)
        print()
        print("[INFO] Starting learning session with fixed configuration...")
        print("[INFO] Behavior monitor: Config loading fixed")
        neo4j_uri = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
        neo4j_password_display = '***' if os.getenv('NEO4J_PASSWORD') else 'NOT_SET'
        print(f"[INFO] Neo4j: {neo4j_uri} (password: {neo4j_password_display})")
        print()

        # 启动会话
        result = await wrapper.start_session(
            canvas_path=canvas_path,
            user_id="default",
            session_name="CS70 Lecture1 Learning Session (Fixed)"
        )

        if result and result.get('success'):
            print("\n" + "=" * 60)
            print("[SUCCESS] Learning session started!")
            print("=" * 60)
            print(f"Session ID: {result['session_id']}")
            print(f"Session Name: {result['session_name']}")
            print()
            print("Memory Systems Status:")
            for system_name, enabled in result['memory_systems'].items():
                status = "[ON] " if enabled else "[OFF]"
                print(f"  {status} {system_name}")

            print()
            print("=" * 60)
            print("System Ready!")
            print("=" * 60)
            print()
            print("Next Steps:")
            print("  1. Canvas file monitoring: Running in background")
            print("  2. All Canvas operations will be recorded")
            print("  3. Use /learning status to check session")
            print("  4. Use /learning stop to end and generate report")
            print()
            print("=" * 60)

            return True
        else:
            error_msg = result.get('error', 'Unknown error') if result else 'No result returned'
            print(f"\n[ERROR] Failed to start learning session")
            print(f"Error: {error_msg}")

            # 显示详细的启动结果
            if result and 'startup_results' in result:
                print()
                print("Detailed Startup Results:")
                for service, service_result in result['startup_results'].items():
                    print(f"\n  {service}:")
                    if isinstance(service_result, dict):
                        for key, value in service_result.items():
                            print(f"    {key}: {value}")
                    else:
                        print(f"    {service_result}")

            return False

    except Exception as e:
        print(f"\n[ERROR] Startup failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def restart_learning_session():
    """同步包装"""
    import asyncio
    try:
        return asyncio.run(restart_learning_session_async())
    except Exception as e:
        print(f"[ERROR] Async execution failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = restart_learning_session()
    sys.exit(0 if success else 1)
