#!/usr/bin/env python3
"""
Test AsyncCanvasProcessor shutdown with monitor_engine set
This replicates the integration test scenario
"""

import sys
import time
import tempfile
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from canvas_progress_tracker.canvas_monitor_engine import CanvasMonitorEngine, MonitorConfig
from canvas_progress_tracker.async_processor import AsyncCanvasProcessor

def test_shutdown_with_monitor():
    """Test that matches integration test scenario"""
    print("="*80)
    print("Testing AsyncCanvasProcessor Shutdown WITH Monitor Engine")
    print("="*80)

    # Create temporary directory (like integration test setUp)
    temp_dir = tempfile.mkdtemp()
    canvas_dir = os.path.join(temp_dir, "canvases")
    os.makedirs(canvas_dir, exist_ok=True)

    try:
        # Create CanvasMonitorEngine (like integration test setUp line 90)
        print("\n[Step 1] Creating CanvasMonitorEngine...")
        config = MonitorConfig(
            base_path=canvas_dir,
            debounce_delay_ms=100
        )
        monitor = CanvasMonitorEngine(canvas_dir, config)
        print(f"  OK Monitor created, DebounceManager has async_processor: {monitor.debounce_manager.async_processor is not None}")

        # Create explicit AsyncCanvasProcessor (like integration test setUp line 94)
        print("\n[Step 2] Creating explicit AsyncCanvasProcessor...")
        processor = AsyncCanvasProcessor(max_workers=4)
        print("  OK Explicit processor created")

        # Now tearDown (like integration test tearDown)
        print("\n[Step 3] Teardown sequence...")

        # Step 3a: clear_all() on DebounceManager
        print("  [3a] Calling debounce_manager.clear_all()...")
        start_time = time.time()
        monitor.debounce_manager.clear_all()
        elapsed = time.time() - start_time
        print(f"    OK clear_all() completed in {elapsed:.2f}s")

        if elapsed > 5.0:
            print(f"    WARNING: clear_all() took {elapsed:.2f}s (expected < 5s)")
            return False

        # Step 3b: shutdown explicit processor
        print("  [3b] Calling processor.shutdown()...")
        start_time = time.time()
        processor.shutdown()
        elapsed = time.time() - start_time
        print(f"    OK processor.shutdown() completed in {elapsed:.2f}s")

        if elapsed > 5.0:
            print(f"    WARNING: processor.shutdown() took {elapsed:.2f}s (expected < 5s)")
            return False

        print("\n" + "="*80)
        print("ALL STEPS PASSED OK")
        print("="*80)
        print("\nConclusion: AsyncCanvasProcessor shutdown works correctly with monitor_engine!")
        return True

    finally:
        # Cleanup
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)

if __name__ == "__main__":
    try:
        success = test_shutdown_with_monitor()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\nERROR TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
