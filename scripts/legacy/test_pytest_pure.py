#!/usr/bin/env python3
"""
纯pytest风格测试（不使用unittest.TestCase）
用于对比是否是unittest兼容层的问题
"""

import tempfile
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

print("[PURE] Module loading started")

from canvas_progress_tracker.canvas_monitor_engine import CanvasMonitorEngine, MonitorConfig

print("[PURE] Module loading completed")


def test_pure_basic():
    """纯pytest测试：基础功能"""
    print("\n[PURE] test_pure_basic() started")
    temp_dir = tempfile.mkdtemp()
    print(f"[PURE] Created temp dir: {temp_dir}")

    try:
        assert os.path.exists(temp_dir)
        print("[PURE] test_pure_basic() passed")
    finally:
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_pure_create_config():
    """纯pytest测试：创建MonitorConfig"""
    print("\n[PURE] test_pure_create_config() started")
    temp_dir = tempfile.mkdtemp()
    canvas_dir = os.path.join(temp_dir, "canvases")
    os.makedirs(canvas_dir, exist_ok=True)

    try:
        config = MonitorConfig(
            base_path=canvas_dir,
            debounce_delay_ms=100
        )
        assert config is not None
        print(f"[PURE] Config created: {config}")
        print("[PURE] test_pure_create_config() passed")
    finally:
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_pure_create_monitor():
    """纯pytest测试：创建CanvasMonitorEngine"""
    print("\n[PURE] test_pure_create_monitor() started")
    temp_dir = tempfile.mkdtemp()
    canvas_dir = os.path.join(temp_dir, "canvases")
    os.makedirs(canvas_dir, exist_ok=True)

    try:
        print("[PURE] Creating MonitorConfig...")
        config = MonitorConfig(
            base_path=canvas_dir,
            debounce_delay_ms=100
        )

        print("[PURE] Creating CanvasMonitorEngine...")
        monitor = CanvasMonitorEngine(canvas_dir, config)

        print(f"[PURE] Monitor created: {monitor}")
        assert monitor is not None

        # Cleanup
        print("[PURE] Cleaning up monitor...")
        if hasattr(monitor, 'sync_scheduler') and monitor.sync_scheduler:
            print("[PURE]   Stopping sync_scheduler...")
            monitor.sync_scheduler.stop(wait_current=False)
        if hasattr(monitor, 'debounce_manager'):
            print("[PURE]   Clearing debounce_manager...")
            monitor.debounce_manager.clear_all()

        print("[PURE] test_pure_create_monitor() passed")
    finally:
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)
