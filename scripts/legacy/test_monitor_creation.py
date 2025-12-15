#!/usr/bin/env python3
"""
精确定位CanvasMonitorEngine创建时的挂起点
"""

import unittest
import tempfile
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from canvas_progress_tracker.canvas_monitor_engine import CanvasMonitorEngine, MonitorConfig

print("[MONITOR] Test file loaded")


class TestMonitorCreation(unittest.TestCase):
    """测试CanvasMonitorEngine创建的各个步骤"""

    def setUp(self):
        print("\n[MONITOR] setUp() started")
        self.temp_dir = tempfile.mkdtemp()
        self.canvas_dir = os.path.join(self.temp_dir, "canvases")
        os.makedirs(self.canvas_dir, exist_ok=True)
        print(f"[MONITOR] Temp dir created: {self.temp_dir}")

    def tearDown(self):
        print("\n[MONITOR] tearDown() started")

        # Cleanup monitor if it exists
        if hasattr(self, 'monitor'):
            print("[MONITOR] Cleaning up monitor...")
            if hasattr(self.monitor, 'sync_scheduler') and self.monitor.sync_scheduler:
                print("[MONITOR]   Stopping sync_scheduler...")
                self.monitor.sync_scheduler.stop(wait_current=False)
            if hasattr(self.monitor, 'debounce_manager'):
                print("[MONITOR]   Clearing debounce_manager...")
                self.monitor.debounce_manager.clear_all()

        # Cleanup temp dir
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        print("[MONITOR] tearDown() completed")

    def test_step1_create_config(self):
        """步骤1：创建MonitorConfig"""
        print("\n[MONITOR] Test: Creating MonitorConfig...")
        config = MonitorConfig(
            base_path=self.canvas_dir,
            debounce_delay_ms=100
        )
        print(f"[MONITOR] MonitorConfig created: {config}")
        assert config is not None

    def test_step2_create_monitor_without_cleanup(self):
        """步骤2：创建CanvasMonitorEngine但不清理"""
        print("\n[MONITOR] Test: Creating CanvasMonitorEngine (no cleanup)...")
        config = MonitorConfig(
            base_path=self.canvas_dir,
            debounce_delay_ms=100
        )
        print("[MONITOR] Config created, about to create monitor...")

        self.monitor = CanvasMonitorEngine(self.canvas_dir, config)

        print(f"[MONITOR] Monitor created: {self.monitor}")
        print(f"[MONITOR]   Has debounce_manager: {hasattr(self.monitor, 'debounce_manager')}")
        print(f"[MONITOR]   Has sync_scheduler: {hasattr(self.monitor, 'sync_scheduler')}")

        assert self.monitor is not None
        print("[MONITOR] Test completed successfully")

    def test_step3_create_and_cleanup_monitor(self):
        """步骤3：创建CanvasMonitorEngine并正确清理"""
        print("\n[MONITOR] Test: Creating CanvasMonitorEngine (with cleanup)...")
        config = MonitorConfig(
            base_path=self.canvas_dir,
            debounce_delay_ms=100
        )
        print("[MONITOR] Config created, about to create monitor...")

        self.monitor = CanvasMonitorEngine(self.canvas_dir, config)

        print(f"[MONITOR] Monitor created, starting cleanup...")

        # Explicit cleanup
        if hasattr(self.monitor, 'sync_scheduler') and self.monitor.sync_scheduler:
            print("[MONITOR]   Stopping sync_scheduler...")
            self.monitor.sync_scheduler.stop(wait_current=False)
            print("[MONITOR]   sync_scheduler stopped")

        if hasattr(self.monitor, 'debounce_manager'):
            print("[MONITOR]   Clearing debounce_manager...")
            self.monitor.debounce_manager.clear_all()
            print("[MONITOR]   debounce_manager cleared")

        print("[MONITOR] Test completed successfully")


if __name__ == "__main__":
    print("[MONITOR] Running with unittest...")
    unittest.main(verbosity=2)
