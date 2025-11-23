#!/usr/bin/env python3
"""
Learning Session Management System Test Suite (English Version)
Test all functionality of the new /learning command system
"""

import os
import sys
import asyncio
import json
import time
import unittest
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import tempfile
import shutil

# Add project path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from learning_session_wrapper import LearningSessionWrapper, LearningSession
    print("Learning session wrapper imported successfully")
except ImportError as e:
    print(f"Import failed: {e}")
    sys.exit(1)

class TestLearningSessionSystem(unittest.TestCase):
    """Learning session system test class"""

    def setUp(self):
        """Test preparation"""
        self.wrapper = LearningSessionWrapper()
        self.test_canvas_path = "tests/test_canvas.canvas"
        self._create_test_canvas()

    def tearDown(self):
        """Test cleanup"""
        asyncio.run(self._cleanup_sessions())
        self._cleanup_test_files()

    def _create_test_canvas(self):
        """Create test canvas file"""
        test_canvas = {
            "nodes": [
                {
                    "id": "test-question-1",
                    "type": "text",
                    "x": 100,
                    "y": 100,
                    "width": 200,
                    "height": 100,
                    "color": "1",
                    "content": "What is a test concept?"
                },
                {
                    "id": "test-yellow-1",
                    "type": "text",
                    "x": 350,
                    "y": 100,
                    "width": 200,
                    "height": 100,
                    "color": "6",
                    "content": "My test understanding"
                }
            ],
            "edges": [
                {
                    "id": "test-edge-1",
                    "fromNode": "test-question-1",
                    "toNode": "test-yellow-1",
                    "label": "Learning path"
                }
            ]
        }

        test_dir = Path("tests")
        test_dir.mkdir(exist_ok=True)

        with open(self.test_canvas_path, 'w', encoding='utf-8') as f:
            json.dump(test_canvas, f, ensure_ascii=False, indent=2)

    def _cleanup_test_files(self):
        """Clean up test files"""
        test_file = Path(self.test_canvas_path)
        if test_file.exists():
            test_file.unlink()

    async def _cleanup_sessions(self):
        """Clean up all sessions"""
        if self.wrapper.current_session:
            session_id = self.wrapper.current_session.session_id
            if session_id in self.wrapper.coordinator.active_sessions:
                await self.wrapper.stop_session(session_id)

    def test_01_start_session_basic(self):
        """Test basic session startup"""
        print("Test 1: Basic session startup")

        async def run_test():
            result = await self.wrapper.start_session(
                canvas_path=self.test_canvas_path,
                session_name="Test Learning Session"
            )

            self.assertTrue(result['success'])
            self.assertIsNotNone(result['session_id'])
            self.assertEqual(result['session_name'], "Test Learning Session")
            self.assertEqual(result['canvas_path'], self.test_canvas_path)

            session = self.wrapper.current_session
            self.assertIsNotNone(session)
            self.assertEqual(session.session_id, result['session_id'])

            print(f"Session started successfully: {result['session_id']}")

        asyncio.run(run_test())

    def test_02_session_status(self):
        """Test session status query"""
        print("Test 2: Session status query")

        async def run_test():
            start_result = await self.wrapper.start_session(
                canvas_path=self.test_canvas_path,
                session_name="Status Test Session"
            )
            self.assertTrue(start_result['success'])

            status_result = await self.wrapper.get_session_status()
            self.assertTrue(status_result['success'])
            self.assertEqual(status_result['session_id'], start_result['session_id'])
            self.assertEqual(status_result['session_name'], "Status Test Session")
            self.assertEqual(status_result['canvas_path'], self.test_canvas_path)

            print(f"Status query successful: session running for {status_result['duration_seconds']:.1f}s")

        asyncio.run(run_test())

    def test_03_stop_session(self):
        """Test session stop"""
        print("Test 3: Session stop")

        async def run_test():
            start_result = await self.wrapper.start_session(
                canvas_path=self.test_canvas_path,
                session_name="Stop Test Session"
            )
            self.assertTrue(start_result['success'])

            await asyncio.sleep(0.5)

            stop_result = await self.wrapper.stop_session(save_report=True)
            self.assertTrue(stop_result['success'])
            self.assertIsNotNone(stop_result['end_time'])

            self.assertIsNone(self.wrapper.current_session)

            print(f"Session stopped successfully: duration {stop_result['duration_seconds']:.1f}s")

        asyncio.run(run_test())

    def test_04_generate_report(self):
        """Test report generation"""
        print("Test 4: Report generation")

        async def run_test():
            start_result = await self.wrapper.start_session(
                canvas_path=self.test_canvas_path,
                session_name="Report Test Session"
            )
            self.assertTrue(start_result['success'])

            await asyncio.sleep(0.5)

            report_result = await self.wrapper.generate_report()
            self.assertTrue(report_result['success'])
            self.assertIsNotNone(report_result['report'])

            report = report_result['report']
            self.assertEqual(report['session_id'], start_result['session_id'])
            self.assertEqual(report['session_name'], "Report Test Session")

            print(f"Report generated successfully: {report['duration_seconds']:.1f}s learning duration")

        asyncio.run(run_test())

    def test_05_error_handling(self):
        """Test error handling"""
        print("Test 5: Error handling")

        async def run_test():
            result1 = await self.wrapper.start_session(
                canvas_path="nonexistent_file.canvas",
                session_name="Error Test Session"
            )

            result2 = await self.wrapper.stop_session("nonexistent_session_id")
            self.assertFalse(result2['success'])

            print(f"Error handling test passed: invalid file handled={result1.get('success', False)}, invalid session handled={not result2['success']}")

        asyncio.run(run_test())

    def test_06_performance(self):
        """Test performance metrics"""
        print("Test 6: Performance metrics")

        async def run_test():
            start_time = time.time()

            result = await self.wrapper.start_session(
                canvas_path=self.test_canvas_path,
                session_name="Performance Test Session"
            )

            startup_time = time.time() - start_time

            self.assertTrue(result['success'])
            self.assertLess(startup_time, 5.0, "Startup time should be less than 5 seconds")

            start_time = time.time()
            status = await self.wrapper.get_session_status()
            query_time = time.time() - start_time

            self.assertTrue(status['success'])
            self.assertLess(query_time, 1.0, "Status query time should be less than 1 second")

            print(f"Performance test passed: startup={startup_time:.3f}s, query={query_time:.3f}s")

        asyncio.run(run_test())

def run_all_tests():
    """Run all tests"""
    print("=" * 60)
    print("Canvas Learning Session Management System - Test Suite")
    print("=" * 60)
    print(f"Test time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    test_suite = unittest.TestSuite()
    tests = unittest.TestLoader().loadTestsFromTestCase(TestLearningSessionSystem)
    test_suite.addTests(tests)

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)

    total_tests = result.testsRun
    failures = len(result.failures)
    errors = len(result.errors)

    print()
    print("=" * 60)
    print("Test Results Summary")
    print("=" * 60)
    print(f"Total tests: {total_tests}")
    print(f"Passed: {total_tests - failures - errors}")
    print(f"Failed: {failures}")
    print(f"Errors: {errors}")
    print(f"Success rate: {((total_tests - failures - errors) / total_tests * 100):.1f}%")

    if failures == 0 and errors == 0:
        print("\nAll tests passed! Learning session management system is ready.")
        return True
    else:
        print(f"\nFound {failures + errors} issues, please check and fix.")
        return False

if __name__ == "__main__":
    success = run_all_tests()

    if success:
        print("\nNext steps:")
        print("1. Integrate into existing slash command system")
        print("2. Conduct user testing")
        print("3. Optimize based on user feedback")
    else:
        print("\nNext steps:")
        print("1. Fix failed test cases")
        print("2. Rerun tests")
        print("3. Integrate after all tests pass")