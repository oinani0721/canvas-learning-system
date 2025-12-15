#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试Graphiti在LearningSessionWrapper中的启动
"""

import asyncio
import sys
import logging

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(levelname)s:%(name)s:%(message)s',
    stream=sys.stdout,
    force=True
)

async def test_graphiti_startup():
    """测试Graphiti启动"""
    print("=" * 70)
    print("[TEST] Testing Graphiti startup in RealServiceLauncher")
    print("=" * 70)

    try:
        from learning_system.real_service_launcher import RealServiceLauncher
        from dataclasses import dataclass
        from datetime import datetime

        # 创建模拟session对象
        @dataclass
        class MockSession:
            session_id: str = "test_session_123"

        session = MockSession()

        print("\n[Step 1] Creating RealServiceLauncher...")
        launcher = RealServiceLauncher()
        print("    [OK] Launcher created")

        print("\n[Step 2] Calling _start_graphiti_real...")
        result = await launcher._start_graphiti_real(
            canvas_path="tests/fixtures/test-basic.canvas",
            session=session
        )

        print("\n[Step 3] Graphiti startup result:")
        print(f"    Success: {result.get('success')}")
        print(f"    Status: {result.get('status')}")
        print(f"    Message: {result.get('message')}")

        if result.get('success'):
            print(f"    Episode ID: {result.get('episode_id', 'N/A')}")
            print(f"    Storage: {result.get('storage', 'N/A')}")
            print("\n[SUCCESS] Graphiti启动成功！")
        else:
            print(f"    Error: {result.get('error', 'Unknown')}")
            print("\n[FAILED] Graphiti启动失败")
            return False

        return True

    except Exception as e:
        print(f"\n[ERROR] Exception occurred: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_graphiti_startup())
    sys.exit(0 if success else 1)
