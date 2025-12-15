#!/usr/bin/env python3
"""
最小化pytest测试，用于定位挂起问题
逐步添加组件，找出导致挂起的具体原因
"""

import unittest
import tempfile
import os
import sys
from pathlib import Path

print("[MINIMAL] Module loading started")

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

print("[MINIMAL] Importing canvas_progress_tracker modules...")
from canvas_progress_tracker.canvas_monitor_engine import CanvasMonitorEngine, MonitorConfig
from canvas_progress_tracker.data_stores import HotDataStore, ColdDataStore
from canvas_progress_tracker.learning_analyzer import LearningAnalyzer
from canvas_progress_tracker.async_processor import AsyncCanvasProcessor
from canvas_progress_tracker.report_generator import LearningReportGenerator

print("[MINIMAL] All imports completed")


class TestMinimal(unittest.TestCase):
    """最小化测试类"""

    @classmethod
    def setUpClass(cls):
        print("\n[MINIMAL] setUpClass() called")

    def setUp(self):
        print("\n[MINIMAL] setUp() called")
        self.temp_dir = tempfile.mkdtemp()
        self.canvas_dir = os.path.join(self.temp_dir, "canvases")
        self.data_dir = os.path.join(self.temp_dir, "data")
        os.makedirs(self.canvas_dir, exist_ok=True)
        os.makedirs(self.data_dir, exist_ok=True)
        print(f"[MINIMAL] Created temp dirs: {self.temp_dir}")

    def tearDown(self):
        print("\n[MINIMAL] tearDown() called")
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        print("[MINIMAL] tearDown() completed")

    @classmethod
    def tearDownClass(cls):
        print("\n[MINIMAL] tearDownClass() called")

    def test_basic(self):
        """基础测试：仅创建临时目录"""
        print("\n[MINIMAL] test_basic() running")
        assert os.path.exists(self.temp_dir)
        print("[MINIMAL] test_basic() passed")

    def test_create_config(self):
        """测试创建MonitorConfig"""
        print("\n[MINIMAL] test_create_config() running")
        config = MonitorConfig(
            base_path=self.canvas_dir,
            debounce_delay_ms=100
        )
        assert config is not None
        print("[MINIMAL] test_create_config() passed")

    def test_create_monitor(self):
        """测试创建CanvasMonitorEngine"""
        print("\n[MINIMAL] test_create_monitor() running")
        config = MonitorConfig(
            base_path=self.canvas_dir,
            debounce_delay_ms=100
        )
        monitor = CanvasMonitorEngine(self.canvas_dir, config)
        assert monitor is not None

        # Cleanup
        if hasattr(monitor, 'sync_scheduler') and monitor.sync_scheduler:
            monitor.sync_scheduler.stop(wait_current=False)
        if hasattr(monitor, 'debounce_manager'):
            monitor.debounce_manager.clear_all()

        print("[MINIMAL] test_create_monitor() passed")


if __name__ == "__main__":
    print("[MINIMAL] Running with unittest...")
    unittest.main()
