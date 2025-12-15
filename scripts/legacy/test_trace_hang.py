#!/usr/bin/env python3
"""
追踪CanvasMonitorEngine创建时的挂起点
添加详细的打印语句来定位exact hang location
"""

import tempfile
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

print("[TRACE] Script started")

print("[TRACE] Importing modules...")
from canvas_progress_tracker.canvas_monitor_engine import CanvasMonitorEngine, MonitorConfig
print("[TRACE] Modules imported successfully")

def test_monitor_creation_with_trace():
    """追踪monitor创建的每一步"""
    print("\n[TRACE] === Test Started ===")

    # Step 1: Create temp directory
    print("[TRACE] Step 1: Creating temp directory...")
    temp_dir = tempfile.mkdtemp()
    canvas_dir = os.path.join(temp_dir, "canvases")
    os.makedirs(canvas_dir, exist_ok=True)
    print(f"[TRACE] Step 1 DONE: {temp_dir}")

    try:
        # Step 2: Create MonitorConfig
        print("[TRACE] Step 2: Creating MonitorConfig...")
        config = MonitorConfig(
            base_path=canvas_dir,
            debounce_delay_ms=100
        )
        print(f"[TRACE] Step 2 DONE: {config}")

        # Step 3: Create CanvasMonitorEngine (THIS IS WHERE IT HANGS)
        print("[TRACE] Step 3: About to create CanvasMonitorEngine...")
        print("[TRACE] Step 3a: Calling CanvasMonitorEngine() constructor...")

        monitor = CanvasMonitorEngine(canvas_dir, config)

        # If we get here, creation succeeded
        print("[TRACE] Step 3 DONE: CanvasMonitorEngine created successfully!")
        print(f"[TRACE] Monitor object: {monitor}")

        # Cleanup
        print("[TRACE] Step 4: Cleaning up...")
        if hasattr(monitor, 'sync_scheduler') and monitor.sync_scheduler:
            print("[TRACE] Step 4a: Stopping sync_scheduler...")
            monitor.sync_scheduler.stop(wait_current=False)
        if hasattr(monitor, 'debounce_manager'):
            print("[TRACE] Step 4b: Clearing debounce_manager...")
            if hasattr(monitor.debounce_manager, 'async_processor') and monitor.debounce_manager.async_processor:
                print("[TRACE] Step 4c: Shutting down async_processor...")
                monitor.debounce_manager.async_processor.shutdown(timeout=5)
            monitor.debounce_manager.clear_all()
        print("[TRACE] Step 4 DONE: Cleanup complete")

        print("\n[TRACE] === Test PASSED ===")

    finally:
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)
        print("[TRACE] Temp directory removed")

if __name__ == "__main__":
    print("[TRACE] Running standalone test...")
    test_monitor_creation_with_trace()
    print("[TRACE] Standalone test completed!")
