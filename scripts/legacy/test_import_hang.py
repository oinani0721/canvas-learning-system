#!/usr/bin/env python3
"""
追踪模块导入时的挂起
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

print("[IMPORT] Step 1: About to import MonitorConfig...")
from canvas_progress_tracker.canvas_monitor_engine import MonitorConfig
print("[IMPORT] Step 1 DONE: MonitorConfig imported")

print("[IMPORT] Step 2: About to import CanvasMonitorEngine...")
from canvas_progress_tracker.canvas_monitor_engine import CanvasMonitorEngine
print("[IMPORT] Step 2 DONE: CanvasMonitorEngine imported")

print("[IMPORT] === All imports successful ===")
