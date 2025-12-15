#!/usr/bin/env python3
"""
Diagnostic test to find where setUp() hangs in integration tests
"""

import sys
import time
import tempfile
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

def test_setup_stepby_step():
    """Test each setUp step individually"""
    print("="*80)
    print("Setup Diagnostic Test")
    print("="*80)

    temp_dir = tempfile.mkdtemp()
    canvas_dir = os.path.join(temp_dir, "canvases")
    data_dir = os.path.join(temp_dir, "data")
    db_path = os.path.join(data_dir, "learning_data.db")

    os.makedirs(canvas_dir, exist_ok=True)
    os.makedirs(data_dir, exist_ok=True)

    try:
        # Step 1: Import MonitorConfig
        print("\n[Step 1] Importing MonitorConfig...")
        start = time.time()
        from canvas_progress_tracker.canvas_monitor_engine import MonitorConfig
        print(f"  OK - {time.time() - start:.2f}s")

        # Step 2: Create MonitorConfig
        print("\n[Step 2] Creating MonitorConfig...")
        start = time.time()
        config = MonitorConfig(
            base_path=canvas_dir,
            debounce_delay_ms=100,
            retry_attempts=3
        )
        print(f"  OK - {time.time() - start:.2f}s")

        # Step 3: Import CanvasMonitorEngine
        print("\n[Step 3] Importing CanvasMonitorEngine...")
        start = time.time()
        from canvas_progress_tracker.canvas_monitor_engine import CanvasMonitorEngine
        print(f"  OK - {time.time() - start:.2f}s")

        # Step 4: Create CanvasMonitorEngine (THIS IS WHERE IT MIGHT HANG)
        print("\n[Step 4] Creating CanvasMonitorEngine...")
        print("  This creates:")
        print("    - DebounceManager (with AsyncCanvasProcessor)")
        print("    - DataSyncScheduler singleton (with HotDataStore & ColdDataStore)")
        start = time.time()
        monitor = CanvasMonitorEngine(canvas_dir, config)
        elapsed = time.time() - start
        print(f"  OK - {elapsed:.2f}s")

        if elapsed > 5.0:
            print(f"  WARNING: CanvasMonitorEngine creation took {elapsed:.2f}s (expected < 5s)")

        # Step 5: Create HotDataStore
        print("\n[Step 5] Creating HotDataStore...")
        start = time.time()
        from canvas_progress_tracker.data_stores import HotDataStore
        hot_store = HotDataStore(Path(data_dir))
        print(f"  OK - {time.time() - start:.2f}s")

        # Step 6: Create ColdDataStore
        print("\n[Step 6] Creating ColdDataStore...")
        start = time.time()
        from canvas_progress_tracker.data_stores import ColdDataStore
        cold_store = ColdDataStore(db_path)
        print(f"  OK - {time.time() - start:.2f}s")

        # Step 7: Create LearningAnalyzer
        print("\n[Step 7] Creating LearningAnalyzer...")
        start = time.time()
        from canvas_progress_tracker.learning_analyzer import LearningAnalyzer
        analyzer = LearningAnalyzer()
        print(f"  OK - {time.time() - start:.2f}s")

        # Step 8: Create AsyncCanvasProcessor
        print("\n[Step 8] Creating AsyncCanvasProcessor...")
        start = time.time()
        from canvas_progress_tracker.async_processor import AsyncCanvasProcessor
        processor = AsyncCanvasProcessor(max_workers=4)
        print(f"  OK - {time.time() - start:.2f}s")

        # Step 9: Create LearningReportGenerator
        print("\n[Step 9] Creating LearningReportGenerator...")
        start = time.time()
        from canvas_progress_tracker.learning_report_generator import LearningReportGenerator
        report_gen = LearningReportGenerator(cold_store)
        print(f"  OK - {time.time() - start:.2f}s")

        print("\n" + "="*80)
        print("ALL SETUP STEPS COMPLETED SUCCESSFULLY!")
        print("="*80)

        # Now tearDown
        print("\n[Teardown] Cleaning up...")

        if hasattr(monitor, 'sync_scheduler') and monitor.sync_scheduler:
            print("  Stopping sync_scheduler...")
            monitor.sync_scheduler.stop(wait_current=False)

        if hasattr(monitor, 'debounce_manager'):
            print("  Clearing debounce_manager...")
            monitor.debounce_manager.clear_all()

        print("  Shutting down processor...")
        processor.shutdown()

        print("  OK - Teardown complete")

        return True

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    success = test_setup_stepby_step()
    sys.exit(0 if success else 1)
