#!/usr/bin/env python3
"""
Standalone test to verify AsyncCanvasProcessor shutdown() works correctly
Tests the poison pill pattern fix for threading deadlock issue
"""

import sys
import time
import logging
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from canvas_progress_tracker.async_processor import AsyncCanvasProcessor

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_async_processor_shutdown():
    """Test AsyncCanvasProcessor shutdown completes in < 5 seconds"""
    print("="*80)
    print("Testing AsyncCanvasProcessor Shutdown (Poison Pill Pattern)")
    print("="*80)

    # Test 1: Empty queue shutdown (simplest case)
    print("\n[Test 1] Testing shutdown with empty queue...")
    processor = AsyncCanvasProcessor(max_workers=4, queue_size=100)

    start_time = time.time()
    processor.shutdown(timeout=10)
    elapsed = time.time() - start_time

    print(f"  [OK] Shutdown completed in {elapsed:.2f}s")
    assert elapsed < 5.0, f"Shutdown took {elapsed:.2f}s (expected < 5.0s)"
    print("  [OK] PASS: Shutdown completed within timeout")

    # Test 2: Shutdown with some tasks
    print("\n[Test 2] Testing shutdown with queued tasks...")
    processor2 = AsyncCanvasProcessor(max_workers=4, queue_size=100)

    # Submit some dummy tasks
    for i in range(10):
        processor2.submit_task(
            canvas_path=f"test_{i}.canvas",
            old_content={"nodes": []},
            new_content={"nodes": [{"id": f"node-{i}"}]}
        )

    # Give workers time to start processing
    time.sleep(0.5)

    start_time = time.time()
    processor2.shutdown(timeout=10)
    elapsed = time.time() - start_time

    print(f"  [OK] Shutdown completed in {elapsed:.2f}s")
    assert elapsed < 5.0, f"Shutdown took {elapsed:.2f}s (expected < 5.0s)"
    print("  [OK] PASS: Shutdown with tasks completed within timeout")

    # Test 3: Multiple rapid shutdown cycles
    print("\n[Test 3] Testing multiple rapid shutdown cycles...")
    for i in range(3):
        processor3 = AsyncCanvasProcessor(max_workers=4, queue_size=100)

        # Submit a few tasks
        for j in range(3):
            processor3.submit_task(
                canvas_path=f"cycle_{i}_task_{j}.canvas",
                old_content={"nodes": []},
                new_content={"nodes": []}
            )

        time.sleep(0.1)

        start_time = time.time()
        processor3.shutdown(timeout=10)
        elapsed = time.time() - start_time

        print(f"  Cycle {i+1}: Shutdown in {elapsed:.2f}s")
        assert elapsed < 5.0, f"Cycle {i+1} shutdown took {elapsed:.2f}s"

    print("  [OK] PASS: All rapid shutdown cycles completed within timeout")

    print("\n" + "="*80)
    print("ALL TESTS PASSED [OK]")
    print("="*80)
    print("\nConclusion: AsyncCanvasProcessor shutdown() poison pill fix is working correctly!")
    return True

if __name__ == "__main__":
    try:
        test_async_processor_shutdown()
        sys.exit(0)
    except AssertionError as e:
        print(f"\n[FAIL] TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
