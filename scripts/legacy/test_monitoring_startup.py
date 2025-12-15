#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试Canvas监控系统启动
快速验证监控系统是否能正常工作
"""

import sys
import os
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_basic_import():
    """测试基本导入"""
    print("[TEST 1] Testing basic module import...")
    try:
        from canvas_progress_tracker import CanvasMonitorEngine
        print("[OK] CanvasMonitorEngine imported successfully")
        return True
    except Exception as e:
        print(f"[FAIL] Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_engine_creation():
    """测试创建监控引擎"""
    print("\n[TEST 2] Testing engine creation...")
    try:
        from canvas_progress_tracker import CanvasMonitorEngine

        # 创建监控引擎
        canvas_path = str(Path("笔记库").resolve())
        engine = CanvasMonitorEngine(canvas_path)
        print(f"[OK] Engine created successfully")
        print(f"     Monitoring path: {canvas_path}")
        return True, engine
    except Exception as e:
        print(f"[FAIL] Engine creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False, None

def test_monitoring_start():
    """测试启动监控"""
    print("\n[TEST 3] Testing monitoring start...")
    try:
        from canvas_progress_tracker import CanvasMonitorEngine

        # 创建并启动监控引擎
        canvas_path = str(Path("笔记库").resolve())
        engine = CanvasMonitorEngine(canvas_path)

        # 启动监控
        success = engine.start_monitoring()

        if success:
            print("[OK] Monitoring started successfully!")
            print(f"     Status: {engine.is_monitoring}")

            # 立即停止 (这只是测试)
            engine.stop_monitoring()
            print("[OK] Monitoring stopped (test completed)")
            return True
        else:
            print("[FAIL] Monitoring failed to start")
            return False

    except Exception as e:
        print(f"[FAIL] Monitoring start failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("="*60)
    print("Canvas Monitoring System Startup Test")
    print("="*60)

    # 测试1: 基本导入
    if not test_basic_import():
        print("\n[FAIL] Basic import test failed")
        return False

    # 测试2: 创建引擎
    success, engine = test_engine_creation()
    if not success:
        print("\n[FAIL] Engine creation test failed")
        return False

    # 测试3: 启动监控
    if not test_monitoring_start():
        print("\n[FAIL] Monitoring start test failed")
        return False

    print("\n" + "="*60)
    print("[SUCCESS] All tests passed! Monitoring system works!")
    print("="*60)
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
