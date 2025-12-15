#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Canvas监控系统 - 后台启动脚本
简化版启动器，直接在后台运行监控系统
"""

import sys
import time
import signal
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 全局变量
monitoring_engine = None
is_running = False

def signal_handler(signum, frame):
    """信号处理器 - 安全停止监控"""
    global monitoring_engine, is_running
    print("\n[INFO] Received stop signal, shutting down...")
    is_running = False
    if monitoring_engine:
        monitoring_engine.stop_monitoring()
    print("[INFO] Monitoring stopped successfully")
    sys.exit(0)

def start_monitoring_background():
    """启动后台监控"""
    global monitoring_engine, is_running

    try:
        from canvas_progress_tracker import CanvasMonitorEngine

        # 创建监控引擎
        canvas_path = str(Path("笔记库").resolve())
        monitoring_engine = CanvasMonitorEngine(canvas_path)

        # 启动监控
        success = monitoring_engine.start_monitoring()

        if success:
            print("="*60)
            print("Canvas Monitoring System Started")
            print("="*60)
            print(f"Status: RUNNING")
            print(f"Monitoring Path: {canvas_path}")
            print(f"Process: Background")
            print("="*60)
            print("Press Ctrl+C to stop monitoring")
            print("")

            is_running = True

            # 保持运行
            while is_running:
                time.sleep(1)

        else:
            print("[ERROR] Failed to start monitoring system")
            return False

    except KeyboardInterrupt:
        print("\n[INFO] User interrupted")
        if monitoring_engine:
            monitoring_engine.stop_monitoring()
        return True

    except Exception as e:
        print(f"[ERROR] Failed to start monitoring: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True

def main():
    """主函数"""
    # 设置信号处理
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # 启动监控
    start_monitoring_background()

if __name__ == "__main__":
    main()
