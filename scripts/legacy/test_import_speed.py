#!/usr/bin/env python3
"""Test import speed of canvas_progress_tracker modules"""

import time
import sys

print("=" * 80)
print("Canvas Progress Tracker Module Import Speed Test")
print("=" * 80)

total_start = time.time()

# Test each module import
modules_to_test = [
    ("canvas_monitor_engine", "from canvas_progress_tracker.canvas_monitor_engine import CanvasMonitorEngine, MonitorConfig"),
    ("data_stores", "from canvas_progress_tracker.data_stores import HotDataStore, ColdDataStore"),
    ("learning_analyzer", "from canvas_progress_tracker.learning_analyzer import LearningAnalyzer"),
    ("async_processor", "from canvas_progress_tracker.async_processor import AsyncCanvasProcessor"),
    ("report_generator", "from canvas_progress_tracker.report_generator import LearningReportGenerator"),
]

for module_name, import_stmt in modules_to_test:
    print(f"\n[Testing] {module_name}...")
    start = time.time()
    try:
        exec(import_stmt)
        elapsed = time.time() - start
        print(f"  [OK] {module_name:30s} - {elapsed:6.2f}s")
    except Exception as e:
        elapsed = time.time() - start
        print(f"  [FAIL] {module_name:30s} - {elapsed:6.2f}s")
        print(f"     Error: {e}")
        sys.exit(1)

total_time = time.time() - total_start
print("\n" + "=" * 80)
print(f"Total import time: {total_time:.2f}s")
print("=" * 80)
